using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl09;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-09 parity (U-21): the prototype's own run (the mechanical bot, seed 1, Traces/prologue_mech_seed1.jsonl.gz, with
    /// DL-09's fields: the cage, its pawl, the balance gauge, the plates, the persist flags, the cable's clock, the tunnel's
    /// triggers, the <c>refuge</c> moment, the act's clock) replayed through Core's <see cref="SceneSim"/> with
    /// <see cref="Dl09Scene.Def"/>, input for input, compared at every 60 Hz step.
    /// <para><b>One window, from a recorded rest.</b> The chapter replay covers DL-09 from #20840 (<see cref="Dl09ChapterProbe"/>,
    /// through DL-08); this window, written before DL-08 was in Core, stays as a check that localises a failure. It starts DL-09 on its own (<see cref="ChapterSim.BeginAt"/> through the scene shim's hand-over) at the first rest in
    /// DL-09, #20879 (he has run off the belt's top and stopped at the first climb's face, x 98.63, still on <c>latched</c>),
    /// and runs to DL-10's first step (#25182): the climbs, both plates into the tray, the ride (settle, lower, shudder, slip,
    /// the catch at 1.95, the pawl thrown in the stall, the bite, caught), Proud, <c>cage</c>, off onto the landing
    /// (<c>landing8</c>), through the antechamber between the arcs, <c>tunnel</c>, the long hopscotch, the city and its moment,
    /// the slow walk and his label, and out to DL-10.</para>
    /// <para><b>Tolerance 1e-6</b> on every continuous value; discrete ones on the same step. The cage's clock (<c>c.t</c>) and
    /// its <c>readyAt</c> count from the world's build, which here is the window's start: the clock is compared from the cage's
    /// first change of phase, <c>readyAt</c> as whether he may board.</para>
    /// </summary>
    public class Dl09TraceTests
    {
        internal const string TraceFile = Dl01TraceTests.TraceFile;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw;
            public bool G, Exited;
            public string Kind, Phase, Cp, Hold, Scene, Cues;
            public int Region;
            public Dl09Sample M;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public int From, To;
        }

        private static Replay _cached;
        private static readonly object Gate = new object();

        /// <summary>The window: from the first rest in DL-09 (the step after it) to DL-10's first step.</summary>
        internal static (int from, int to) Window(Trace t)
        {
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-09"));
            int rest = first;
            while (!(t.Steps[rest].Vx == 0 && t.Steps[rest].G && t.Steps[rest].Act == null && !t.Steps[rest].Mt)) rest++;
            return (rest + 1, t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-10")));
        }

        internal static Replay Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var (from, to) = Window(t);
                var r = new Replay { From = from, To = to };
                SlippingCage09 rules = null;
                int deaths0 = t.Steps[from - 1].Dn9 ?? 0;
                r.Sim = TraceReplay.Run(t, Dl09Scene.Def(), t.Steps[from - 1].Cp, false, from, to, (p, sim) =>
                {
                    rules ??= (SlippingCage09)sim.Rules;
                    var cues = new StringBuilder();
                    foreach (var c in sim.Cues) cues.Append(cues.Length > 0 ? "," : "").Append(c);
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Hold = sim.Motor.Hold == HoldKind.None ? null : "item", Scene = sim.Chapter.Current?.Id, Cues = cues.ToString(),
                        M = Dl09Sample.Of(rules, sim.Chapter, deaths0),
                    });
                }, handover: true);
                return _cached = r;
            }
        }

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_HasDl09_AndTheWindowStartsAtARecordedRest()
        {
            var t = Trace.Load(TraceFile);
            var (from, to) = Window(t);
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-09"));
            Assert.Equal(20840, first);
            Assert.Null(t.Steps[first - 1].Cp9);                                                   // DL-09's fields start in DL-09
            Assert.Equal("top", t.Steps[first].Cp9);
            Assert.Equal(20880, from);
            var rest = t.Steps[from - 1];
            Assert.Equal((0.0, true, "latched"), (rest.Vx, rest.G, rest.Cp));
            Assert.Equal(98.62968, rest.X, 9);
            Assert.Equal(25182, to);
            Assert.StartsWith("DL-10", t.Steps[to].Scene);
            Assert.Equal("caught", t.Steps[to].Cp9);                                               // and end on the step he leaves it
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        /// <summary>x, y, z, vx, yaw, grounded and the region: the climbs, the carries, the ride (a step behind the cage), the hops.</summary>
        [Fact]
        public void X_Y_Z_Vx_Yaw_Grounded_AndRegion_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "z", -w.P.Z, w.Z);
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
                if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
                if (w.Region != w.P.Region) bad.Add($"#{w.P.I} region {w.P.Region} vs {w.Region}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>He rides one step behind the cage (<c>game.y = c.y</c> at #4, before <c>updateCage</c>, L5081).</summary>
        [Fact]
        public void InTheCage_HeStandsOnItsFloorAsItWasAtTheStepsStart()
        {
            var rows = Run().Rows;
            int n = 0;
            for (int k = 1; k < rows.Count; k++)
                if (rows[k].Kind == "cage" && rows[k - 1].Kind == "cage") { Assert.Equal(rows[k - 1].M.CageY, rows[k].Y, 12); n++; }
            Assert.True(n > 250, n.ToString());
        }

        // ---- (b) acts and holds -----------------------------------------------------------------------------------------
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var t = Trace.Load(TraceFile);
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in Run().Rows)
            {
                string want = ExpectedAct(t, w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in KeyActs) Assert.Contains(a, seen);
        }

        internal static readonly string[] KeyActs =
        {
            "mantle:", "dl09.plate0:Approach", "dl09.plate0:Clip", "dl09.plate1:Clip", "Place:Approach", "Place:Turn", "Place:Clip",
            "cage:act", "quirk:Proud", "hopscotch:act", "awe:turn", "awe:act", "awe:back", "quirk:CheckLabel",
        };

        // ---- (c) checkpoints, the scene, the way on ----------------------------------------------------------------------
        /// <summary><c>cage</c> on the upper landing (L4949), <c>landing8</c> off the caught cage (L4950), <c>tunnel</c> (L3421).</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            foreach (var w in rows) if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(21341, rows.Find(w => w.Cp == "cage").P.I);
            Assert.Equal(22421, rows.Find(w => w.Cp == "landing8").P.I);
            Assert.Equal(22634, rows.Find(w => w.Cp == "tunnel").P.I);
        }

        /// <summary>DL-09 holds him to <c>UPONLY.x0</c>; on DL-10's first step he is past the (one-scene) chapter.</summary>
        [Fact]
        public void HoldsHim_ToDl10_OnThePrototypesStep()
        {
            var rows = Run().Rows;
            for (int k = 0; k < rows.Count - 1; k++)
            {
                Assert.Equal("DL-09", rows[k].Scene);
                Assert.False(rows[k].Exited, "#" + rows[k].P.I);
            }
            var last = rows[rows.Count - 1];
            Assert.True(last.Exited);
            Assert.Null(last.Scene);
            Assert.True(last.X >= Dl09Scene.LabelX1);
        }

        /// <summary>The ride's shakes (shudder 0.35, the catch 0.45, the bite 0.5) and the city's moment, on their steps.</summary>
        [Fact]
        public void Cues_AreRaisedOnThePrototypesSteps()
        {
            var cues = new List<(int, string)>();
            foreach (var w in Run().Rows) if (w.Cues.Length > 0) foreach (var c in w.Cues.Split(',')) cues.Add((w.P.I, c));
            foreach (var (step, cue) in KeyCues) Assert.Contains((step, cue), cues);
        }

        internal static readonly (int, string)[] KeyCues = { (22099, "shake:35"), (22193, "shake:45"), (22201, "shake:50"), (23563, "moment:refuge") };

        // ---- (d) mechanisms ---------------------------------------------------------------------------------------------
        /// <summary>
        /// The cage (phase, y, slip speed, clock, pawl, caught once, step-out, ready), the balance gauge, the plates (state, x,
        /// base, seat), <c>persist.cw</c>, the cage's danger, the cable (its clock, shocks, the first-touch flag), the tunnel's
        /// triggers, the moment's clock and cut, the act's clock, deaths and the respawn: every step of the window.
        /// </summary>
        [Fact]
        public void Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var phases = new HashSet<string>();
            int compared = 0;
            bool clockKnown = false;
            string before = null;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.Cp9 == null) continue;
                compared++;
                if (before != null && p.Cp9 != before) clockKnown = true;
                before = p.Cp9;
                Dl09Sample.Compare(bad, p, w.M, clockKnown);
                phases.Add(w.M.Phase);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(25182 - 20880 + 1, compared);
            Assert.Equal(new HashSet<string> { "top", "settle", "lower", "shudder", "slip", "stall", "bite", "caught" }, phases);
        }

        // ---- Dump ---------------------------------------------------------------------------------------------------
        /// <summary>Debugging aid, not a test: the window side by side as TSV.</summary>
        internal static void Dump(string path)
        {
            var t = Trace.Load(TraceFile);
            var sb = new StringBuilder("i\tpx\tcx\tpy\tcy\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tpcp\tccp\tpph\tcph\tpcy\tccy\tin\n");
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(R(w.X)).Append('\t').Append(p.Y).Append('\t').Append(R(w.Y))
                  .Append('\t').Append(p.Vx).Append('\t').Append(R(w.Vx)).Append('\t').Append(p.Yaw).Append('\t').Append(R(w.Yaw))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0)
                  .Append('\t').Append(ExpectedAct(t, p)).Append('\t').Append(CoreAct(w)).Append('\t').Append(p.Cp).Append('\t').Append(w.Cp)
                  .Append('\t').Append(p.Cp9).Append('\t').Append(w.M.Phase).Append('\t').Append(p.Cy9).Append('\t').Append(R(w.M.CageY))
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        /// <summary>
        /// The prototype's act as Core names it: a plate's lift by the plate he then carries, the set-down into the tray (the
        /// motor's Place on the tray loader), the cage, the hopscotch and the city (DL-09's scene acts), quirks by their clip.
        /// </summary>
        internal static string ExpectedAct(Trace t, TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                case "liftItem":
                {
                    string who = null;
                    for (int i = t.FirstIndex(q => q.I == p.I); i < t.Steps.Count && who == null; i++)
                    {
                        var q = t.Steps[i];
                        if (q.P0s9 == "carried") who = "dl09.plate0";
                        else if (q.P1s9 == "carried") who = "dl09.plate1";
                    }
                    return who + ":" + (phase == "approach" ? "Approach" : "Clip");
                }
                case "loadTray": return "Place:" + (phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : "Clip");
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);
    }

    /// <summary>DL-09's mechanisms and rules' state at one step, as the recorder's DL-09 fields name it (the window and the chapter probe).</summary>
    internal struct Dl09Sample
    {
        public string Phase, P0s, P1s, ActKind;
        public double CageY, CageV, CageT, Needle, P0x, P0b, P1x, P1b, ArcPhase, ActT, RespawnAt;
        public double? Moment;
        public int? P0q, P1q;
        public bool Thrown, CaughtOnce, NeedExit, Ready, Cw, Danger, ShockedOnce, Hopped, Awed, Cut;
        public int Shocked, Deaths;

        public static Dl09Sample Of(SlippingCage09 r, ChapterSim sim, int deaths0)
        {
            var c = r.Cage;
            var flags = sim.Checkpoints.Flags;
            var act = sim.Act;
            return new Dl09Sample
            {
                Phase = PhaseName(c.State), CageY = c.Y, CageV = c.SlipSpeed, CageT = c.Elapsed, Thrown = r.Pawl.Thrown,
                CaughtOnce = c.CaughtOnce, NeedExit = c.NeedExit, Ready = c.ReadyIn < -1e-9, Needle = r.Tray.Needle,
                P0s = PlateName(r.Plate0), P0x = r.Plate0.X, P0b = r.Plate0.BaseY, P0q = r.Plate0.State == ItemState.Placed ? r.Plate0.Slot : (int?)null,
                P1s = PlateName(r.Plate1), P1x = r.Plate1.X, P1b = r.Plate1.BaseY, P1q = r.Plate1.State == ItemState.Placed ? r.Plate1.Slot : (int?)null,
                Cw = flags.Has(StoryFlags.CounterweightsStowed), Danger = flags.Has(StoryFlags.CageDanger), ShockedOnce = flags.Has(StoryFlags.ShockedOnce),
                Shocked = r.Shocked, ArcPhase = r.Arc1.Phase, Hopped = r.Hopped, Awed = r.Awed,
                Moment = r.Moment.Time(sim.Clock), Cut = r.Moment.Cut,
                ActKind = act?.Kind.Name, ActT = act?.T ?? double.NaN,
                Deaths = deaths0 + sim.Deaths, RespawnAt = sim.RespawnAt,
            };
        }

        /// <summary>The prototype's <c>c.phase</c>.</summary>
        public static string PhaseName(SlippingCageState s)
        {
            string n = s.ToString();
            return char.ToLowerInvariant(n[0]) + n.Substring(1);
        }

        /// <summary>The prototype's plate <c>state</c>.</summary>
        public static string PlateName(CarriedItem p) => p.State == ItemState.Floor ? "floor" : p.State == ItemState.Carried ? "carried" : p.State == ItemState.Placed ? "tray" : p.State.ToString();

        /// <param name="clockKnown">The cage's clock counts from a phase change Core has seen (else from the world's build, which may differ).</param>
        public static void Compare(List<string> bad, TraceStep p, Dl09Sample w, bool clockKnown)
        {
            int i = p.I;
            if (p.Cp9 != w.Phase) bad.Add($"#{i} cage {p.Cp9} vs {w.Phase}");                                 // L5020–L5050
            Check(bad, i, "cage.y", p.Cy9.Value, w.CageY);
            Check(bad, i, "cage.v", p.Cv9.Value, w.CageV);
            if (clockKnown) Check(bad, i, "cage.t", p.Ct9.Value, w.CageT);
            if ((p.Th9 ?? false) != w.Thrown) bad.Add($"#{i} thrown {p.Th9} vs {w.Thrown}");                   // L5085–L5093
            if ((p.Co9 ?? false) != w.CaughtOnce) bad.Add($"#{i} caughtOnce {p.Co9} vs {w.CaughtOnce}");
            if ((p.Ne9 ?? false) != w.NeedExit) bad.Add($"#{i} needExit {p.Ne9} vs {w.NeedExit}");
            bool ready = p.Clk > p.Ry9.Value;
            if (ready != w.Ready) bad.Add($"#{i} ready {ready} vs {w.Ready}");
            Check(bad, i, "needle", p.Nd9.Value, w.Needle);                                                     // L5054
            Plate(bad, i, 0, p.P0s9, p.P0x9, p.P0b9, p.P0q9, w.P0s, w.P0x, w.P0b, w.P0q);
            Plate(bad, i, 1, p.P1s9, p.P1x9, p.P1b9, p.P1q9, w.P1s, w.P1x, w.P1b, w.P1q);
            if ((p.Cw9 >= 2) != w.Cw) bad.Add($"#{i} persist.cw {p.Cw9} vs {w.Cw}");                             // L4436
            if ((p.Dg9 ?? false) != w.Danger) bad.Add($"#{i} cageDanger {p.Dg9} vs {w.Danger}");                 // L5037, L5046
            if ((p.So9 ?? false) != w.ShockedOnce) bad.Add($"#{i} shockedOnce {p.So9} vs {w.ShockedOnce}");
            if (p.Sk9 != w.Shocked) bad.Add($"#{i} shocked {p.Sk9} vs {w.Shocked}");
            Check(bad, i, "arc clock", p.Ta9.Value, w.ArcPhase);                                                 // L7398
            if ((p.Hp9 ?? false) != w.Hopped) bad.Add($"#{i} hopped {p.Hp9} vs {w.Hopped}");
            if ((p.Aw9 ?? false) != w.Awed) bad.Add($"#{i} awed {p.Aw9} vs {w.Awed}");
            if (p.Mt9.HasValue != w.Moment.HasValue) bad.Add($"#{i} moment {p.Mt9} vs {w.Moment}");
            else if (p.Mt9.HasValue) Check(bad, i, "moment", p.Mt9.Value, w.Moment.Value);
            if ((p.Mc9 ?? false) != w.Cut) bad.Add($"#{i} momentCut {p.Mc9} vs {w.Cut}");
            if (w.ActKind != null && w.ActKind != "death")                                                      // a scene act's clock is a.t
            {
                if (!p.At9.HasValue) bad.Add($"#{i} act clock - vs {w.ActT}");
                else Check(bad, i, "act.t", p.At9.Value, w.ActT);
            }
            if (p.Dn9 != w.Deaths) bad.Add($"#{i} deaths {p.Dn9} vs {w.Deaths}");
            Check(bad, i, "respawnAt", p.Ra9.Value, w.RespawnAt);
        }

        private static void Plate(List<string> bad, int i, int n, string ps, double? px, double? pb, int? pq, string cs, double cx, double cb, int? cq)
        {
            if (ps != cs) bad.Add($"#{i} plate{n} {ps} vs {cs}");
            Check(bad, i, $"plate{n}.x", px.Value, cx);
            Check(bad, i, $"plate{n}.base", pb.Value, cb);
            if (pq != cq) bad.Add($"#{i} plate{n}.seat {pq} vs {cq}");
        }
    }
}
