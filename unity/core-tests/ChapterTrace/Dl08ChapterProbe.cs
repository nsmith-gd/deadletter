using System;
using System.Collections.Generic;
using System.Text.Json;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl08;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-08 in the chapter replay: on every step from the residential doorway (#17677, <c>goods</c>) to DL-09's first
    /// (#20840, the end of the belt): the goods trolley (x, velocity), the pan's load, the platform (h, fall speed, latched,
    /// lurching), the pawl's lever and dip, the returns belt (state, its warning clock, the next crate's wait), the turn flaps
    /// and every crate (type, state, x, y, z, t, spin) (the recorder's DL-08 fields, tools/sim/record_trace.mjs). DL-08 is
    /// walked into on the run from the gallery, so it has no scene replay of its own: this chapter replay is its proof.
    /// <para>The crates' draws are the prototype's: its <c>Math.random</c> is the page's, shared with everything else, so no
    /// seed reproduces them; the recorder found each crate's three LCG states (<c>rs8</c>) and this probe feeds them to the
    /// belt (<see cref="ReturnsBelt.Draws"/>) in spawn order. When and where a crate spawns is still the belt's own.</para>
    /// </summary>
    internal sealed class Dl08ChapterProbe : ChapterTraceProbe<Dl08ChapterProbe.S>
    {
        internal struct S
        {
            public double Tx, Tv, Pan, H, V, Lever, Dip, BeltT, Next, Flaps;
            public bool Latched, Lurch;
            public string Belt;
            public double[][] Crates;
        }

        private Handbrake08 _rules;
        private int _draws;

        public override string Scene => "DL-08";
        public override int FirstStep => 17677;
        public override IReadOnlyList<string> KeyActs => new[]
        {
            "dl08.trolley:Approach", "dl08.trolley:Clip", "dl08.platform:Teeter", "dl08.pawl:Approach", "dl08.pawl:Turn",
            "dl08.pawl:StepIn", "dl08.pawl:Clip", "dl08.pawl:StepOut", "quirk:Proud", "mantle:",
        };
        /// <summary>
        /// DL-07's gallery collapse hits behind him (shake 0.6, #17689: it gave way at #17662); he steps onto the unlatched
        /// platform (shake 0.3) and it crashes down its 0.1 m dip (0.55 · v / 3 = 0.22); the pawl's click (0.22) and the
        /// <c>latch</c> sting.
        /// </summary>
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[]
        {
            (17689, "shake:60"), (18447, "shake:30"), (18625, "shake:22"), (18625, "music:latch"),
        };

        public override void Bind(ChapterSim sim, Trace t)
        {
            foreach (var s in sim.Def.Scenes) if (s.Id == Scene) _rules = (Handbrake08)sim.RulesOf(s);
            var draws = new Queue<double>();
            foreach (var p in t.Steps)
                if (p.Rs8 != null) foreach (long s in p.Rs8) draws.Enqueue(s / 2147483647.0);   // the LCG's value, s / M (L2667)
            _draws = draws.Count;
            _rules.Belt.Draws = () => draws.Dequeue();
        }

        protected override S Sample(ChapterSim sim)
        {
            var r = _rules;
            var b = r.Belt;
            var crates = new double[b.Count][];
            for (int i = 0; i < b.Count; i++)
            {
                var c = b.At(i);
                crates[i] = new[] { c.Type, (double)c.State, c.X, c.Y, c.Z, c.T, c.Spin };
            }
            return new S
            {
                Tx = r.Trolley.X, Tv = r.Trolley.Velocity, Pan = r.Pan.Load,
                H = r.Platform.H, V = r.Platform.FallSpeed, Latched = r.Platform.Latched, Lurch = r.Platform.Lurching,
                Lever = r.Pawl.LeverDeg, Dip = r.Pawl.Dip,
                Belt = b.State == ReturnsBeltState.Idle ? "idle" : b.State == ReturnsBeltState.Warn ? "warn" : "run",
                BeltT = b.T, Next = b.Next, Flaps = b.FlapSwing, Crates = crates,
            };
        }

        /// <summary>
        /// DL-08's acts as Core names them: the grab by the trolley (its own face, from its left), the pawl's lever act by the
        /// pawl, the Teeter by the platform (<see cref="Dl08TeeterAct"/>); a quirk by its clip; a climb as the motor's.
        /// </summary>
        public override string ExpectedAct(Trace t, TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                case "grab": return (p.X < p.Tx8 ? "dl08.trolley:" : "Grab:") + (phase == "approach" ? "Approach" : "Clip");
                case "pawl":
                    return "dl08.pawl:" + (phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : phase == "in" ? "StepIn" : phase == "act" ? "Clip" : "StepOut");
                case "teeter": return "dl08.platform:Teeter";
                default: return kind + ":" + phase;
            }
        }

        private static readonly string[] CrateStates = { "chute", "belt", "turn" };

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, crates = 0, last = run.Rows[run.RowAfter(Scene)].P.I;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k];
                if (p.Tx8 == null || p.I < FirstStep || p.I > last) continue;
                compared++;
                Check(bad, p.I, "trolley.x", p.Tx8.Value, w.Tx);
                Check(bad, p.I, "trolley.v", p.Tv8.Value, w.Tv);
                Check(bad, p.I, "pan", p.Pn8.Value, w.Pan);
                Check(bad, p.I, "platform.h", p.Ph8.Value, w.H);
                Check(bad, p.I, "platform.v", p.Pv8.Value, w.V);
                if (p.La8 != w.Latched) bad.Add($"#{p.I} latched {p.La8} vs {w.Latched}");
                if (p.Lu8 != w.Lurch) bad.Add($"#{p.I} lurch {p.Lu8} vs {w.Lurch}");
                Check(bad, p.I, "pawl.lever", p.Pw8.Value, w.Lever);
                Check(bad, p.I, "pawl.dip", p.Pd8.Value, w.Dip);
                if (p.Bs8 != w.Belt) bad.Add($"#{p.I} belt {p.Bs8} vs {w.Belt}");
                Check(bad, p.I, "belt.t", p.Bt8.Value, w.BeltT);
                Check(bad, p.I, "belt.next", p.Bn8.Value, w.Next);
                Check(bad, p.I, "flaps", p.Fl8.Value, w.Flaps);
                using var doc = JsonDocument.Parse(p.Cr8);
                var arr = doc.RootElement;
                if (arr.GetArrayLength() != w.Crates.Length) { bad.Add($"#{p.I} crates {arr.GetArrayLength()} vs {w.Crates.Length}"); continue; }
                int i = 0;
                foreach (var c in arr.EnumerateArray())
                {
                    var cw = w.Crates[i++];
                    crates++;
                    if (c[0].GetInt32() != (int)cw[0]) bad.Add($"#{p.I} crate{i} type {c[0]} vs {cw[0]}");
                    if (c[1].GetString() != CrateStates[(int)cw[1]]) bad.Add($"#{p.I} crate{i} state {c[1]} vs {CrateStates[(int)cw[1]]}");
                    Check(bad, p.I, $"crate{i}.x", c[2].GetDouble(), cw[2]);
                    Check(bad, p.I, $"crate{i}.y", c[3].GetDouble(), cw[3]);
                    Check(bad, p.I, $"crate{i}.z", -c[4].GetDouble(), cw[4]);                   // Unity z = −three z
                    Check(bad, p.I, $"crate{i}.t", c[5].GetDouble(), cw[5]);
                    Check(bad, p.I, $"crate{i}.spin", c[6].GetDouble(), cw[6]);
                }
            }
            Assert.Equal(20840, last);                                                          // DL-09's first step: the end of the belt
            Assert.Equal(20840 - 17677 + 1, compared);
            Assert.True(crates > 400, crates.ToString());
            Assert.Equal(6, _draws);                                                            // two crates in the window, three draws each
        }
    }
}
