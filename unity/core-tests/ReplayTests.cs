using System;
using System.Globalization;
using DeadLetter.Core.Simulation.Replay;
using DeadLetter.Core.Simulation.Replay.Scripts;
using Xunit;
using Xunit.Abstractions;

namespace DeadLetter.Core.Tests
{
    /// <summary>U-18 (#15): the bot.js port, its JSONL, and DL-01 played headless start to finish.</summary>
    public class ReplayTests
    {
        private readonly ITestOutputHelper _out;
        public ReplayTests(ITestOutputHelper output) { _out = output; }

        /// <summary>The prototype's DL-01 split in its latest mechanical run (results_moments_mechanical.jsonl: DL-02 − DL-01).</summary>
        public const double PrototypeMechanicalDl01 = 129.98 - 92.82;

        [Theory]
        [InlineData(1u, 0.63, 0.00)]      // every *_mechanical.jsonl
        [InlineData(201u, 0.44, 0.43)]    // results_first_playthrough.jsonl
        [InlineData(202u, 0.13, 0.96)]
        [InlineData(220u, 0.02, 0.98)]
        [InlineData(101u, 0.14, 0.76)]    // results_chapter1_first_playthrough.jsonl
        [InlineData(43u, 1.00, 0.28)]     // results_expansion_attendance_first_playthrough.jsonl
        public void APlayersSeed_DrawsTheSamePlayerAsBotJs(uint seed, double skill, double curious)
        {
            var p = new PlayerModel(seed, mechanical: false);
            Assert.Equal(skill, Math.Round(p.Skill, 2));
            Assert.Equal(curious, Math.Round(p.Curious, 2));
        }

        [Fact]
        public void Mulberry32_MatchesBotJsBitForBit()
        {
            var r = new Mulberry32(1);
            Assert.Equal(0.6270739405881613, r.Next());           // bot.js R() for seed 1, first two draws
            Assert.Equal(0.002735721180215478, r.Next());
        }

        [Fact]
        public void TheResultLine_HasEveryFieldSummarisePyReads()
        {
            var r = new SimResult { Seed = 7, Skill = 0.634, Curious = 0.1, Done = true, Error = null, Mode = "play" };
            r.Mark("opening", 0); r.Mark("play", 0.004); r.Mark("DL-01", 0.02); r.Mark("DL-01", 99); r.Mark("end", 37.126);
            r.Events.Add("13.3 shutter \"up\"");
            string j = r.ToJson();
            Assert.StartsWith("{\"seed\":7,\"player\":{\"skill\":0.63,\"curious\":0.1},\"marks\":{\"opening\":0,\"play\":0,\"DL-01\":0.02,\"end\":37.13}", j);
            Assert.Contains("\"events\":[\"13.3 shutter \\\"up\\\"\"]", j);
            Assert.Contains("\"error\":null", j);
            Assert.Contains("\"deaths\":0,\"found\":0", j);
            Assert.Contains("\"engine\":\"core\"", j);
            Assert.DoesNotContain("\n", j);
        }

        private SimResult PlayDl01(uint seed, bool mechanical)
        {
            var rig = new Dl01SimRig();
            var r = SimRun.Play(rig, new Dl01WakeScript(new PlayerModel(seed, mechanical)));
            _out.WriteLine(r.ToJson());
            return r;
        }

        /// <summary>
        /// Two differences between the Core port and the web build that the replay found, each a locked-input beat the
        /// prototype has and Core doesn't yet. The bot waits both out (it waits for <c>!G.act</c>):
        /// the latch's Flinch, 1.6 s after Pull f39 (L1875–L1876; Core ends the act at f39, <c>Latch.cs</c> EndFrame), and the
        /// <c>Proud</c> quirk after the crank, 40 f less the 0.05 s end test (L1894–L1895, L3852), plus turning back to
        /// face +x first at 8 rad/s (π/2 rad, L1893). Raised on #16 for U-10/U-11.
        /// </summary>
        public const double LatchFlinch = 1.6, ProudQuirk = 40 / 24.0 - 0.05 + Math.PI / 2 / 8;

        /// <summary>The prototype's mechanical DL-01 beats (results_moments_mechanical.jsonl events, from play; DL-02 from the marks).</summary>
        private static readonly (string beat, double proto, double known)[] Beats =
        {
            ("shutter up", 13.3, LatchFlinch),
            ("cart in the trench", 17.6, 0),
            ("door open", 31.0, ProudQuirk),
            ("DL-02", PrototypeMechanicalDl01, 0),
        };

        private static double EventTime(SimResult r, string beat)
        {
            if (beat == "DL-02") return r.MarkOr("DL-02") - r.MarkOr("DL-01");
            foreach (var e in r.Events)
                if (e.EndsWith(" " + beat)) return double.Parse(e.Substring(0, e.IndexOf(' ')), CultureInfo.InvariantCulture);
            return double.NaN;
        }

        /// <summary>
        /// #15's acceptance: DL-01's mechanical solve, headless, compared with the prototype's beat by beat. Each stretch
        /// between beats matches the web build to 0.25 s once the known differences above are taken off; anything else
        /// is a new divergence and fails here.
        /// </summary>
        [Fact]
        public void Dl01_MechanicalSolve_PassesHeadless_AndMatchesThePrototypeBeatByBeat()
        {
            var r = PlayDl01(1, mechanical: true);
            Assert.Null(r.Error);
            Assert.True(r.Done);
            Assert.Equal(0, r.Deaths);
            Assert.True(r.HasMark("cp shutter") && r.HasMark("cp hall") && r.HasMark("cp door"));
            double prevCore = 0, prevProto = 0, known = 0;
            foreach (var (beat, proto, k) in Beats)
            {
                double core = EventTime(r, beat);
                Assert.False(double.IsNaN(core), beat);
                known += k;
                _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0,-20} core {1,6:0.00}  prototype {2,6:0.00}  known {3,5:0.00}",
                    beat, core, proto, known));
                Assert.InRange((core - prevCore) - (proto - prevProto - k), -0.25, 0.25);
                prevCore = core; prevProto = proto;
            }
            double t = r.MarkOr("DL-02") - r.MarkOr("DL-01");
            _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "DL-01 mechanical: core {0:0.00} s, prototype {1:0.00} s, known differences {2:0.00} s",
                t, PrototypeMechanicalDl01, known));
        }

        [Fact]
        public void Dl01_MechanicalSolve_IsDeterministic()
        {
            Assert.Equal(StripWall(PlayDl01(1, true).ToJson()), StripWall(PlayDl01(1, true).ToJson()));
        }

        /// <summary>
        /// With <c>DL_SIM_OUT=&lt;dir&gt;</c> set (and optionally <c>DL_SIM_SEEDS=2,3,6</c>), writes the mechanical run and 20 first playthroughs (seeds 201–220, the
        /// prototype's batch) as <c>results_core_dl01_mechanical.jsonl</c> and <c>results_core_dl01_first_playthrough.jsonl</c>
        /// for <c>tools/sim/summarise.py</c>. Without it, it only checks the batch completes.
        /// </summary>
        [Fact]
        public void Dl01_Batch_WritesJsonlForSummarisePy()
        {
            string dir = Environment.GetEnvironmentVariable("DL_SIM_OUT");
            var mech = new System.Text.StringBuilder();
            var first = new System.Text.StringBuilder();
            var m = SimRun.Play(new Dl01SimRig(), new Dl01WakeScript(new PlayerModel(1, true)));
            Assert.Null(m.Error);
            mech.Append(m.ToJson()).Append('\n');
            string seeds = Environment.GetEnvironmentVariable("DL_SIM_SEEDS");   // e.g. "2,3,6"; default 201–220
            var list = new System.Collections.Generic.List<uint>();
            if (string.IsNullOrEmpty(seeds)) for (uint k = 201; k <= 220; k++) list.Add(k);
            else foreach (var part in seeds.Split(',')) list.Add(uint.Parse(part.Trim(), CultureInfo.InvariantCulture));
            foreach (uint seed in list)
            {
                var r = SimRun.Play(new Dl01SimRig(), new Dl01WakeScript(new PlayerModel(seed, false)));
                Assert.Null(r.Error);
                first.Append(r.ToJson()).Append('\n');
            }
            if (string.IsNullOrEmpty(dir)) return;
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "results_core_dl01_mechanical.jsonl"), mech.ToString());
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "results_core_dl01_first_playthrough.jsonl"), first.ToString());
        }

        private static string StripWall(string j) => System.Text.RegularExpressions.Regex.Replace(j, "\"wall\":[^,]*,", "");

        /// <summary>First-playthrough players (seeded hesitation and mistakes, incl. the trench fail) all finish DL-01.</summary>
        [Theory]
        [InlineData(201u)] [InlineData(202u)] [InlineData(203u)] [InlineData(204u)] [InlineData(205u)]
        [InlineData(206u)] [InlineData(207u)] [InlineData(208u)] [InlineData(209u)] [InlineData(210u)]
        public void Dl01_FirstPlaythroughs_Finish(uint seed)
        {
            var r = PlayDl01(seed, mechanical: false);
            Assert.Null(r.Error);
            Assert.True(r.MarkOr("DL-02") - r.MarkOr("DL-01") >= PrototypeMechanicalDl01 * 0.9);
        }
    }
}
