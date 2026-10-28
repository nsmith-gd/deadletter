using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Simulation.Replay;
using DeadLetter.Core.Simulation.Replay.Scripts;
using Xunit;
using Xunit.Abstractions;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-18 (#15): bot.js ported to Core, playing DL-01 live on U-20's <see cref="ChapterSim"/>. Where the golden trace
    /// (<see cref="Dl01TraceTests"/>) replays the prototype's recorded inputs, these tests let the C# bot choose its own,
    /// which is what scenes without a prototype trace (DL-18+) and first-playthrough distributions need.
    /// </summary>
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

        /// <summary>The prologue's world from a new game, play starting at the opening's last step (as the prototype's bot sees it).</summary>
        internal static ChapterSimTarget Prologue(double clock = 0)
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = clock };
            return new ChapterSimTarget(sim).NewGame(fromOpening: true);
        }

        private SimResult PlayDl01(uint seed, bool mechanical)
        {
            var r = SimRun.Play(Prologue(), new PrologueScript(new PlayerModel(seed, mechanical), "DL-01"));
            _out.WriteLine(r.ToJson());
            return r;
        }

        /// <summary>
        /// Known differences between Core and the web build, each a locked-input beat the bot waits out, in seconds
        /// (drop each when its fix lands). None left on DL-01: U-20's rules play the latch's Flinch and the Proud quirk.
        /// </summary>
        private static readonly (string beat, double proto, double known)[] Beats =
        {
            ("shutter up", 13.3, 0),
            ("cart in the trench", 17.6, 0),
            ("door open", 31.0, 0),
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
        /// #15's acceptance: DL-01's mechanical solve, headless on <see cref="ChapterSim"/>, compared with the prototype's
        /// (results_moments_mechanical.jsonl) beat by beat, each stretch to 0.1 s (events are logged to 0.1 s).
        /// </summary>
        [Fact]
        public void Dl01_MechanicalSolve_PassesHeadless_AndMatchesThePrototypeBeatByBeat()
        {
            var r = PlayDl01(1, mechanical: true);
            Assert.Null(r.Error);
            Assert.True(r.Done);
            Assert.Equal(0, r.Deaths);
            Assert.True(r.HasMark("cp shutter") && r.HasMark("cp hall") && r.HasMark("cp door"));
            double prevCore = 0, prevProto = 0;
            foreach (var (beat, proto, k) in Beats)
            {
                double core = EventTime(r, beat);
                Assert.False(double.IsNaN(core), beat);
                _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0,-20} core {1,6:0.00}  prototype {2,6:0.00}", beat, core, proto));
                Assert.InRange((core - prevCore) - (proto - prevProto - k), -0.11, 0.11);
                prevCore = core; prevProto = proto;
            }
            _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "DL-01 mechanical: core {0:0.00} s, prototype {1:0.00} s",
                r.MarkOr("DL-02") - r.MarkOr("DL-01"), PrototypeMechanicalDl01));
        }

        /// <summary>
        /// The prologue's mechanical solve (DL-01 to DL-06) on one <see cref="ChapterSim"/>, from the prototype's clock at
        /// play (the DL-02 press runs on the game clock): each scene starts on the step it starts in the recorded run
        /// (its <c>sceneName</c> changes in prologue_mech_seed1), to the 0.01 s the marks keep.
        /// </summary>
        [Fact]
        public void Prologue_MechanicalSolve_EntersEachSceneWhenThePrototypeDid()
        {
            var t = Trace.Load(Dl01TraceTests.TraceFile);
            int play = t.FirstIndex(p => p.Mode == "play");
            var r = SimRun.Play(Prologue(t.Steps[play - 1].Clk), new PrologueScript(new PlayerModel(1, mechanical: true)));
            _out.WriteLine(r.ToJson());
            Assert.Null(r.Error);
            Assert.True(r.Done);
            double play0 = r.MarkOr("play");
            foreach (var scene in new[] { "DL-02", "DL-03", "DL-04", "DL-05", "DL-06" })
            {
                int k = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith(scene + " ", StringComparison.Ordinal));
                double proto = t.Steps[k].Clk - t.Steps[play].Clk, core = r.MarkOr(scene) - play0;
                _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0} from play: core {1,7:0.00} s  prototype {2,7:0.000} s", scene, core, proto));
                Assert.InRange(core - proto, -0.011, 0.011);
            }
            Assert.Equal(0, r.Deaths);
        }

        /// <summary>First-playthrough players through the whole ported prologue: their mistakes and hesitations still finish it.</summary>
        [Theory]
        [InlineData(201u)] [InlineData(202u)] [InlineData(203u)] [InlineData(204u)] [InlineData(205u)]
        [InlineData(206u)] [InlineData(207u)] [InlineData(208u)] [InlineData(209u)] [InlineData(210u)] [InlineData(216u)]
        public void Prologue_FirstPlaythroughs_Finish(uint seed)
        {
            var r = SimRun.Play(Prologue(), new PrologueScript(new PlayerModel(seed, mechanical: false)));
            _out.WriteLine(r.ToJson());
            Assert.Null(r.Error);
            Assert.True(r.Done);
        }

        [Fact]
        public void Dl01_MechanicalSolve_IsDeterministic()
        {
            Assert.Equal(StripWall(PlayDl01(1, true).ToJson()), StripWall(PlayDl01(1, true).ToJson()));
        }

        private static string StripWall(string j) => System.Text.RegularExpressions.Regex.Replace(j, "\"wall\":[^,]*,", "");

        /// <summary>
        /// The port, step for step: the C# bot, playing DL-01 live, presses what bot.js pressed in the prototype's recorded
        /// run (Traces/prologue_mech_seed1.jsonl.gz) at every step from the first of play to the end of the passage.
        /// Its choices read the scene's state, so this checks the port of bot.js and Core's responses together.
        /// </summary>
        [Fact]
        public void Dl01_TheLiveBot_GivesTheRecordedBotsInput_AtEveryStep() => LiveBotParity("DL-01", 2232);

        /// <summary>
        /// The same, on through DL-06: the prologue as far as Core has ported it, in one <see cref="ChapterSim"/>, until the
        /// bot's DL-06 script ends (the belt runs to the exit).
        /// </summary>
        [Fact]
        public void Prologue_TheLiveBot_GivesTheRecordedBotsInput_AtEveryStep() => LiveBotParity("DL-06", 12250);

        /// <param name="steps">How many steps the window holds (the recorded run's, from play to the script's end).</param>
        private void LiveBotParity(string lastScene, int steps)
        {
            var t = Trace.Load(Dl01TraceTests.TraceFile);
            int play = t.FirstIndex(p => p.Mode == "play");
            var target = Prologue(t.Steps[play - 1].Clk);
            var bot = new PrologueScript(new PlayerModel(1, mechanical: true), lastScene);
            bot.Begin(target);
            var diffs = new List<string>();
            int k = play;
            for (; k < t.Steps.Count && !bot.Done; k++)
            {
                var mine = bot.Tick();
                if (bot.Done) break;
                var theirs = t.Steps[k].Input;
                if (!SameInput(mine, theirs) && diffs.Count < 10)
                    diffs.Add(string.Format(CultureInfo.InvariantCulture, "step {0} (+{1}): core {2} vs prototype {3}  [{4}; core x={5:0.000} act={6} hold={7}]",
                        t.Steps[k].I, k - play, Show(mine), Show(theirs), t.Steps[k], target.X, target.Act, target.Hold));
                target.Step(mine);
            }
            foreach (var d in diffs) _out.WriteLine(d);
            _out.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0} steps compared ({1:0.00} s of play); bot error: {2}; events: {3}",
                k - play, (k - play) / 60.0, bot.Out.Error ?? "none", string.Join(" | ", bot.Out.Events)));
            Assert.Empty(diffs);
            Assert.Null(bot.Out.Error);
            Assert.True(bot.Done, "the bot finished " + lastScene + " inside the recorded run");
            Assert.Equal(steps, k - play);
        }

        private static bool SameInput(MotorInput a, MotorInput b) =>
            a.Move == b.Move && a.JumpPressed == b.JumpPressed && a.JumpHeld == b.JumpHeld && a.UsePressed == b.UsePressed
            && a.UseHeld == b.UseHeld && a.RunModifierHeld == b.RunModifierHeld;

        private static string Show(MotorInput m) =>
            "move " + m.Move.ToString(CultureInfo.InvariantCulture) + (m.JumpPressed ? " J" : "") + (m.JumpHeld ? " j" : "")
            + (m.UsePressed ? " U" : "") + (m.RunModifierHeld ? " R" : "");

        /// <summary>First-playthrough players (seeded hesitation and mistakes, incl. the trench fail) all finish DL-01.</summary>
        [Theory]
        [InlineData(201u)] [InlineData(202u)] [InlineData(203u)] [InlineData(204u)] [InlineData(205u)]
        [InlineData(206u)] [InlineData(207u)] [InlineData(208u)] [InlineData(209u)] [InlineData(210u)]
        public void Dl01_FirstPlaythroughs_Finish(uint seed)
        {
            var r = PlayDl01(seed, mechanical: false);
            Assert.Null(r.Error);
            Assert.True(r.MarkOr("DL-02") - r.MarkOr("DL-01") >= PrototypeMechanicalDl01 - 0.5);
        }

        /// <summary>
        /// With <c>DL_SIM_OUT=&lt;dir&gt;</c> set (and optionally <c>DL_SIM_SEEDS=2,3,6</c>), writes the prologue's mechanical
        /// run (from the recorded run's clock at play, as the prototype's) and first playthroughs (default seeds 201–220, the
        /// prototype's batch) as <c>results_core_prologue_mechanical.jsonl</c> and <c>results_core_prologue_first_playthrough.jsonl</c>
        /// for <c>tools/sim/summarise.py</c>. Without it, it only checks the batch completes.
        /// </summary>
        [Fact]
        public void Prologue_Batch_WritesJsonlForSummarisePy()
        {
            string dir = Environment.GetEnvironmentVariable("DL_SIM_OUT");
            var t = Trace.Load(Dl01TraceTests.TraceFile);
            var mech = new StringBuilder();
            var first = new StringBuilder();
            var m = SimRun.Play(Prologue(t.Steps[t.FirstIndex(p => p.Mode == "play") - 1].Clk), new PrologueScript(new PlayerModel(1, true)));
            Assert.Null(m.Error);
            mech.Append(m.ToJson()).Append('\n');
            string seeds = Environment.GetEnvironmentVariable("DL_SIM_SEEDS");
            var list = new List<uint>();
            if (string.IsNullOrEmpty(seeds)) for (uint k = 201; k <= 220; k++) list.Add(k);
            else foreach (var part in seeds.Split(',')) list.Add(uint.Parse(part.Trim(), CultureInfo.InvariantCulture));
            foreach (uint seed in list)
            {
                var r = SimRun.Play(Prologue(), new PrologueScript(new PlayerModel(seed, false)));
                Assert.Null(r.Error);
                first.Append(r.ToJson()).Append('\n');
            }
            if (string.IsNullOrEmpty(dir)) return;
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "results_core_prologue_mechanical.jsonl"), mech.ToString());
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "results_core_prologue_first_playthrough.jsonl"), first.ToString());
        }
    }
}
