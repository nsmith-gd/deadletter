using System.Collections.Generic;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl09;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-09 in the chapter replay: on every step from DL-09's first (#20840, off the top of DL-08's returns belt) to DL-10's
    /// first (#25182): the cage (phase, y, slip speed, its clock from the world's build at <c>start</c>, the pawl, caught once,
    /// step-out, ready), the balance gauge, the plates, <c>persist.cw</c>, the cage's danger, the cable (its clock, shocks, the
    /// first touch), the tunnel's triggers, the <c>refuge</c> moment, the act's clock, deaths and the respawn (the recorder's
    /// DL-09 fields, tools/sim/record_trace.mjs), compared as <see cref="Dl09TraceTests"/> compares them in its own window.
    /// <para><b>Not registered yet</b>: the chapter replay reaches DL-09 only through DL-08, which is being ported in parallel.
    /// Once DL-08 is in <see cref="ChapterDefs.Prologue"/> (between DL-07 and DL-09) and its probe is registered, add
    /// <c>new Dl09ChapterProbe()</c> after DL-08's in <see cref="ChapterTraceProbes.Prologue"/>.</para>
    /// </summary>
    internal sealed class Dl09ChapterProbe : ChapterTraceProbe<Dl09Sample>
    {
        private SlippingCage09 _rules;

        public override string Scene => "DL-09";
        public override int FirstStep => 20840;
        public override IReadOnlyList<string> KeyActs => Dl09TraceTests.KeyActs;
        /// <summary>The shudder (0.35), the catch (0.45), the bite (0.5) and the city's moment.</summary>
        public override IReadOnlyList<(int step, string cue)> KeyCues => Dl09TraceTests.KeyCues;

        public override void Bind(ChapterSim sim, Trace t)
        {
            foreach (var s in sim.Def.Scenes) if (s.Id == Scene) _rules = (SlippingCage09)sim.RulesOf(s);
        }

        protected override Dl09Sample Sample(ChapterSim sim) => Dl09Sample.Of(_rules, sim, 0);

        public override string ExpectedAct(Trace t, TraceStep p) => Dl09TraceTests.ExpectedAct(t, p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, last = run.Rows[run.RowAfter(Scene)].P.I;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P;
                if (p.Cp9 == null || p.I < FirstStep || p.I > last) continue;
                compared++;
                Dl09Sample.Compare(bad, p, Samples[k], clockKnown: true);                      // one world from start: c.t counts from #1768 here too
            }
            Assert.Equal(25182, last);                                                          // DL-10's first step
            Assert.Equal(25182 - 20840 + 1, compared);
        }
    }
}
