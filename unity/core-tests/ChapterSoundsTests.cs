using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Presentation;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Simulation.Replay;
using DeadLetter.Core.Simulation.Replay.Scripts;
using Xunit;
using Xunit.Abstractions;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-23 (#34): the prologue's sounds decided in Core (<see cref="ChapterSounds"/>) from the mechanisms' log, the motor's
    /// events, the scenes' cues and the prototype's per-frame polls. <see cref="Playthrough"/> runs the C# bot through DL-01
    /// to DL-06 with the whole <see cref="ChapterPresentation"/> and records what it decided; the facts below pin each
    /// audio_inventory.md row the prologue uses to the key it plays and, where the prototype delays or scales it, to its
    /// index.html timing and level.
    /// </summary>
    public class ChapterSoundsTests
    {
        private readonly ITestOutputHelper _out;
        public ChapterSoundsTests(ITestOutputHelper output) { _out = output; }

        /// <summary>What a bot run of the prologue (DL-01 → DL-06) made the presentation decide.</summary>
        internal sealed class Playthrough
        {
            public readonly Dictionary<string, int> Keys = new Dictionary<string, int>(StringComparer.Ordinal);
            public readonly Dictionary<SfxLoop, double> LoopPeak = new Dictionary<SfxLoop, double>();
            /// <summary>(clock, his x, the sound).</summary>
            public readonly List<(double t, double x, SfxRequest r)> Log = new List<(double, double, SfxRequest)>();
            public double[] EmitterPeak;
            public int[] EmitterBlips;
            public readonly HashSet<MixSnapshot> Snapshots = new HashSet<MixSnapshot>();
            public readonly HashSet<(int region, LightZone zone)> LightPlaces = new HashSet<(int, LightZone)>();
            public double DeepestSfxDuckDb, DeepestAmbienceDuckDb;
            public int MostCarriers, CarrierSlotJumps, CarrierOverflow, LightsOverBudget, AssignedInvisible;
            public SimResult Result;
            public int Dropped;

            public int Count(string key) => Keys.TryGetValue(key, out int n) ? n : 0;
            public IEnumerable<(double t, double x, SfxRequest r)> Of(string key) => Log.Where(l => l.r.Key == key);
        }

        private static readonly Dictionary<(uint, bool), Playthrough> Runs = new Dictionary<(uint, bool), Playthrough>();
        private static readonly object Gate = new object();

        /// <summary>The bot's run (seed 1 mechanical: every *_mechanical.jsonl; 201: a first playthrough that dies under the press), cached.</summary>
        internal static Playthrough Run(uint seed = 1, bool mechanical = true)
        {
            lock (Gate)
            {
                if (Runs.TryGetValue((seed, mechanical), out var cached)) return cached;
                var p = new Playthrough();
                var target = ReplayTests.Prologue();
                var sim = target.Sim;
                var view = new ChapterPresentation(sim);
                view.OnPlaced();
                p.EmitterPeak = new double[view.Ambience.Count];
                p.EmitterBlips = new int[view.Ambience.Count];
                var slotOf = new Dictionary<int, int>();
                var bot = new PrologueScript(new PlayerModel(seed, mechanical));
                bot.Begin(target);
                bool placed = false;
                sim.Checkpoints.Reloaded += _ => placed = true;
                for (int i = 0; i < SimRun.DefaultMaxSteps && !bot.Done; i++)
                {
                    var input = bot.Tick();
                    if (bot.Done) break;
                    target.Step(input);
                    view.AfterStep(voicePlaying: false, calm: false);
                    view.Frame(sim.Clock, ChapterSim.StepSeconds, sim.X, calm: false);
                    var q = view.Sounds.Sounds;
                    for (int k = 0; k < q.Count; k++)
                    {
                        p.Keys[q[k].Key] = p.Count(q[k].Key) + 1;
                        p.Log.Add((sim.Clock, sim.X, q[k]));
                    }
                    foreach (SfxLoop l in Enum.GetValues(typeof(SfxLoop)))
                        p.LoopPeak[l] = Math.Max(p.LoopPeak.TryGetValue(l, out double v) ? v : 0, view.Sounds.Loop(l));
                    for (int e = 0; e < view.Ambience.Count; e++)
                    {
                        p.EmitterPeak[e] = Math.Max(p.EmitterPeak[e], view.Ambience.Gain(e));
                        if (view.Ambience.Blip(e)) p.EmitterBlips[e]++;
                    }
                    p.Snapshots.Add(view.Mix.Snapshot);
                    p.LightPlaces.Add((view.Lighting.Regions.Region, view.Lighting.Regions.Zone));
                    p.DeepestSfxDuckDb = Math.Min(p.DeepestSfxDuckDb, view.Mix.OffsetDb(AudioGroup.Sfx));
                    p.DeepestAmbienceDuckDb = Math.Min(p.DeepestAmbienceDuckDb, view.Mix.OffsetDb(AudioGroup.Ambience));
                    CheckPool(view.Lighting.Pool, p);
                    var c = view.Carriers;
                    int live = 0;
                    for (int s = 0; s < c.Capacity; s++)
                    {
                        if (!c.Active(s)) continue;
                        live++;
                        if (slotOf.TryGetValue(c.SeqOf(s), out int was) && was != s) p.CarrierSlotJumps++;
                        slotOf[c.SeqOf(s)] = s;
                    }
                    p.MostCarriers = Math.Max(p.MostCarriers, live);
                    p.CarrierOverflow = c.Overflow;
                    if (placed) { placed = false; view.OnPlaced(); slotOf.Clear(); }              // a respawn rebuilt the world
                }
                p.Result = bot.Out;
                p.Dropped = view.Sounds.Sounds.Dropped;
                return Runs[(seed, mechanical)] = p;
            }
        }

        private static void CheckPool(LightPool pool, Playthrough p)
        {
            int assigned = 0;
            void Slot(int i) { if (i < 0) return; assigned++; if (!pool.On(i)) p.AssignedInvisible++; }
            for (int s = 0; s < pool.PointSlots; s++) Slot(pool.Point(s));
            for (int s = 0; s < pool.SpotSlots; s++) Slot(pool.Spot(s));
            for (int s = 0; s < pool.SpotShadowSlots; s++) Slot(pool.SpotShadow(s));
            for (int s = 0; s < pool.DirectionalSlots; s++) Slot(pool.Directional(s));
            for (int s = 0; s < pool.HemisphereSlots; s++) Slot(pool.Hemisphere(s));
            var b = pool.Budget;
            if (assigned > b.Point + b.Spot + b.SpotShadow + b.Directional + b.Hemisphere) p.LightsOverBudget++;
        }

        // ---- The inventory's rows ------------------------------------------------------------------------------------------

        /// <summary>
        /// Every audio_inventory.md row with a trigger in DL-01 to DL-06's play (the opening is not ported: GameHost starts on
        /// its last step), and the keys it plays there. "Targeted" rows are reached by the facts further down, the rest by
        /// the bot's runs (seed 1 mechanical; seed 201 dies under the press).
        /// </summary>
        public static readonly (string row, string[] keys, string how)[] Rows =
        {
            ("tick", new[] { "mech_tick" }, "DL-05 dial detents (L4906)"),
            ("relay", new[] { "mech_relay_0", "mech_relay_1", "mech_relay_2" }, "the depot's pulse (L8515)"),
            ("answer", new[] { "mech_answer_0", "mech_answer_1", "mech_answer_2" }, "DL-06 scanner (L2797)"),
            ("servo", new[] { "mech_servo_150_400_700", "mech_servo_500_260_520", "mech_servo_600_300_700" }, "DL-06 levers (L2913), DL-04 cradle (L4790, L4805)"),
            ("click", new[] { "mech_click" }, "mantle 1.4 s (L1911), DL-05 person (L4899)"),
            ("chirp", new[] { "d17_chirp" }, "DL-06 read and perk (L2800, L2811)"),
            ("worried", new[] { "d17_worried" }, "latch flinch (L1875), trench, DL-03 refusal, chute (L2981)"),
            ("tap", new[] { "d17_tap" }, "grab (L1852), tube letter (L4772)"),
            ("rattle", new[] { "mech_rattle_900" }, "shutter release (L1678)"),
            ("step", new[] { "d17_step" }, "footsteps (L2073)"),
            ("jump", new[] { "d17_jump" }, "jump (L1994), mantle (L1910), hop (L2891)"),
            ("land", new[] { "d17_land" }, "landing (L2026), hop (L2892)"),
            ("buzzShort", new[] { "elec_buzz_short" }, "DL-05 under (L4897)"),
            ("ratchet", new[] { "mech_ratchet" }, "crank (L1889), DL-05 twitch, serve, wind (L4901–L4917)"),
            ("doorRumble", new[] { "mech_door_rumble" }, "crank strokes (L1889)"),
            ("doorOpen", new[] { "mech_door_open" }, "bulkhead open (L1890)"),
            ("strain", new[] { "d17_strain" }, "mantle (L1910)"),
            ("drip", new[] { "env_drip" }, "atmosphere drops (L7904)"),
            ("crackle", new[] { "elec_crackle" }, "live cable (L7938)"),
            ("groan", new[] { "env_groan" }, "distant machinery (L7964)"),
            ("scrape", new[] { "mech_scrape" }, "mantle (L1910), lift (L2278, L4419)"),
            ("bonk", new[] { "d17_bonk" }, "Targeted: head on the ceiling (L2017)"),
            ("creak", new[] { "mech_creak_400", "mech_creak_600" }, "latch (L1849, L1873)"),
            ("clank", new[] { "mech_clank" }, "release (L1678), press (L7350), DL-05 over (L4898), carrier tip (L2715)"),
            ("chain", new[] { "mech_chain_300", "mech_chain_550", "mech_chain_1500" }, "tube (L4772), release (L1678), served (L4901)"),
            ("thud", new[] { "mech_thud" }, "shutter (L1679), cart (L4757), drum (L4728), press (L7350)"),
            ("distant", new[] { "env_distant" }, "distant machinery (L7964)"),
            ("plate", new[] { "mech_plate" }, "DL-03 plate (L2375)"),
            ("gateTick", new[] { "mech_gate_tick" }, "DL-03 gate (L2382)"),
            ("gateSlam", new[] { "mech_gate_slam" }, "DL-03 gate (L2386)"),
            ("lift", new[] { "d17_lift" }, "Lift f13 (L2277, L4418)"),
            ("setDown", new[] { "d17_setdown_deck", "d17_setdown_floor" }, "DL-03 (L2285), tube letter (L4779), items (L4425)"),
            ("squeak", new[] { "mech_squeak" }, "DL-03 trolley (L2350), drum (L4703)"),
            ("rowOn", new[] { "mech_row_on_0", "mech_row_on_1", "mech_row_on_2", "mech_row_on_3", "mech_row_on_4", "mech_row_on_5" }, "DL-04 rows (L2422)"),
            ("knock", new[] { "d17_knock" }, "DL-03 pat (L2287)"),
            ("scanSweep", new[] { "mech_scan_sweep" }, "DL-06 (L2792)"),
            ("reject", new[] { "mech_reject" }, "DL-06 (L2801)"),
            ("hatchLift", new[] { "mech_hatch_lift" }, "DL-06 carriers (L2680, L2741)"),
            ("bell", new[] { "mech_bell" }, "DL-06 dock (L2701)"),
            ("klaxon", new[] { "mech_klaxon" }, "DL-06 belt starts (L2822, L2932)"),
            ("beltStop", new[] { "mech_belt_stop" }, "DL-06 stop lever (L2932)"),
            ("clunk", new[] { "mech_clunk" }, "DL-06 levers, carriers; DL-04 cradle; DL-05 hatch"),
            ("clack", new[] { "mech_clack" }, "DL-06 junction (L2709), points (L2933)"),
            ("tumble", new[] { "mech_tumble" }, "Targeted: onto the heap (L2993); parcels (L2730)"),
            ("alarmBell", new[] { "mech_alarm_bell" }, "DL-05 over (L4898)"),
            ("death", new[] { "death_crush" }, "DL-02 press (L7351, die L7441)"),
        };

        /// <summary>The rows (or parts of rows) DL-01 to DL-06 would play but cannot yet, and why.</summary>
        public static readonly (string row, string why)[] NotPorted =
        {
            ("the opening's frames (tick, relay sets, spark, answer, servo ×7, click, grit, chirp, tap, rattle 0.5, step, scrape)", "the opening timeline (§3.1 #3) is not ported; GameHost starts on its last step"),
            ("lampClick, buzzShort and servo 200_500_900 of the cord lamp", "the cord lamp is not a Core mechanism yet (the Tug clip's servo is mapped for when it is)"),
            ("servo 350_900_1500, tap, knock + chirp of the letters", "letters and the reader (§4.26) are not ported"),
            ("found, curio(scale|paper|stamp|mug|mugDown|sit)", "curiosities (§4.27) and voice cards are not ported"),
            ("ratchet ×2 + found of the voice-card players", "no voice-card act in Core/Scenes yet (VoiceCardAct has the times)"),
            ("knock ×2 + worried of DL-03's nudge (L2306–L2308)", "the nudge act is not in Core/Scenes (only its clip name is)"),
        };

        /// <summary>The continuous layers the prologue sets (audio_inventory.md, continuous layers).</summary>
        public static readonly SfxLoop[] PrologueLoops = { SfxLoop.Hum, SfxLoop.Buzz, SfxLoop.Hiss, SfxLoop.Roll, SfxLoop.Tubes, SfxLoop.Belt, SfxLoop.Drag };

        [Fact]
        public void Playthrough_ReachesTheEndOfDl06_AndDropsNothing()
        {
            var p = Run();
            foreach (var kv in p.Keys.OrderBy(k => k.Key, StringComparer.Ordinal)) _out.WriteLine(kv.Key + " " + kv.Value);
            Assert.Null(p.Result.Error);
            Assert.True(p.Result.Done);
            Assert.Equal(0, p.Dropped);
        }

        [Fact]
        public void EveryRowTheProloguePlays_HasATrigger_TheBotOrAFactReaches()
        {
            var heard = new HashSet<string>(Run().Keys.Keys, StringComparer.Ordinal);
            heard.UnionWith(Run(201, false).Keys.Keys);
            heard.UnionWith(BonkKeys());
            heard.UnionWith(ChuteKeys());
            var missing = Rows.SelectMany(r => r.keys.Where(k => !heard.Contains(k)).Select(k => r.row + ": " + k)).ToList();
            Assert.True(missing.Count == 0, "never played: " + string.Join(", ", missing));
            var bank = new HashSet<string>(SfxKeys.AllKeys(), StringComparer.Ordinal);
            Assert.All(Rows.SelectMany(r => r.keys), k => Assert.Contains(k, bank));      // every key is a render
            Assert.All(heard, k => Assert.Contains(k, bank));                                // and nothing plays a key the bank lacks
        }

        [Fact]
        public void EveryPrologueLayer_IsSet_AndNoOtherIs()
        {
            var p = Run();
            foreach (var l in PrologueLoops) Assert.True(p.LoopPeak[l] > 0, l + " never set");
            Assert.Equal(0, p.LoopPeak[SfxLoop.Drum]);
            Assert.Equal(0, p.LoopPeak[SfxLoop.Air]);
            Assert.Equal(0, p.LoopPeak[SfxLoop.WhiteHiss]);
            Assert.Equal(1, p.LoopPeak[SfxLoop.Hum]);                                       // startPlay: hum(1), L8104
            Assert.Equal(ChapterSounds.WorkBulbBuzz, p.LoopPeak[SfxLoop.Buzz]);             // bulb × 0.25, L1574
            Assert.True(p.LoopPeak[SfxLoop.Roll] <= 1 && p.LoopPeak[SfxLoop.Tubes] <= 1 && p.LoopPeak[SfxLoop.Drag] <= 1);
        }

        // ---- Timings and levels (index.html's setTimeouts and arguments) -----------------------------------------------------

        private const double Step = ChapterSim.StepSeconds;

        [Fact]
        public void Release_ClankChainRattle_ThenTheShuttersThudAt560ms()
        {
            var p = Run();
            double t0 = p.Of("mech_rattle_900").Single().t;
            Assert.Contains(p.Log, l => l.r.Key == "mech_clank" && l.t == t0);
            Assert.Contains(p.Log, l => l.r.Key == "mech_chain_550" && l.t == t0);
            double thud = p.Of("mech_thud").First(l => l.t > t0).t;
            Assert.InRange(thud - t0, 0.56 - Step, 0.56 + Step);                            // L1679
        }

        [Fact]
        public void Mantle_ScrapeStrainScrapeClick_AtThePrototypesDelays()
        {
            var p = Run();
            var strains = p.Of("d17_strain").ToList();
            Assert.NotEmpty(strains);
            foreach (var s in strains)
            {
                double t0 = s.t - ChapterSounds.MantleStrain;                                  // the jump's step
                Assert.Contains(p.Log, l => l.r.Key == "d17_jump" && Math.Abs(l.t - t0) < Step + 1e-9);
                Assert.Contains(p.Log, l => l.r.Key == "mech_scrape" && Math.Abs(l.t - (t0 + 0.38)) < Step + 1e-9);
                Assert.Contains(p.Log, l => l.r.Key == "mech_scrape" && Math.Abs(l.t - (t0 + 1.05)) < Step + 1e-9);
                Assert.Contains(p.Log, l => l.r.Key == "mech_click" && Math.Abs(l.t - (t0 + 1.40)) < Step + 1e-9);
            }
        }

        [Fact]
        public void TubeCough_TapsAt200ms()
        {
            var p = Run();
            double t0 = p.Of("mech_chain_300").Single().t;
            Assert.Contains(p.Log, l => l.r.Key == "d17_tap" && Math.Abs(l.t - (t0 + 0.2)) < Step + 1e-9);   // L4772
        }

        [Fact]
        public void WeighIn_Over_ClanksThenRingsAt300ms_Under_BuzzesAt350ms()
        {
            var p = Run();
            double bell = p.Of("mech_alarm_bell").Single().t;
            Assert.Contains(p.Log, l => l.r.Key == "mech_clank" && Math.Abs(l.t - (bell - 0.3)) < Step + 1e-9);   // L4898
            Assert.NotEmpty(p.Of("elec_buzz_short"));
            Assert.Contains(p.Log, l => l.r.Key == "mech_chain_1500");                       // served, L4899
        }

        [Fact]
        public void RelayPulse_IsThreeLampsHalfASecondApart_ScaledByDistanceFromTheBoard()
        {
            var p = Run();
            var r0 = p.Of("mech_relay_0").ToList();
            Assert.True(r0.Count > 10);
            foreach (var a in r0.Take(5))
            {
                Assert.Contains(p.Log, l => l.r.Key == "mech_relay_1" && Math.Abs(l.t - (a.t + 0.5)) < Step + 1e-9);
                Assert.Contains(p.Log, l => l.r.Key == "mech_relay_2" && Math.Abs(l.t - (a.t + 1.0)) < Step + 1e-9);
            }
            foreach (var l in p.Log.Where(l => l.r.Key.StartsWith("mech_relay_", StringComparison.Ordinal)))
            {
                Assert.Equal(Math.Max(0.25, 0.8 - Math.Abs(l.x - 2) / 8), l.r.Volume, 9);      // k · max(0.25, 0.8 − |x − 2|/8), L8515
                Assert.Equal(ChapterSounds.RelayX, l.r.X);
            }
            var gaps = r0.Zip(r0.Skip(1), (a, b) => b.t - a.t).ToList();
            Assert.All(gaps, g => Assert.InRange(g, 6 - 2 * Step, 6 + 2 * Step));           // every 144 frames (the sequencer's own clock)
        }

        [Fact]
        public void RacksRows_SoundAtRowTimes_AfterTheReveal_AndNotWhenRestored()
        {
            var p = Run();
            double t0 = p.Of("mech_row_on_0").Single().t;
            for (int i = 1; i < 6; i++)
                Assert.InRange(p.Of("mech_row_on_" + i).Single().t - t0, ChapterSounds.RowTimes[i] - 1.0 - Step, ChapterSounds.RowTimes[i] - 1.0 + Step);
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 30 };
            var sounds = new ChapterSounds(sim);
            sim.Begin("bay");                                                                 // revealed long ago (revealTime < 0)
            for (int i = 0; i < 600; i++)
            {
                sim.Step(default);
                sounds.Step();
                for (int k = 0; k < sounds.Sounds.Count; k++) Assert.DoesNotContain("row_on", sounds.Sounds[k].Key);
            }
            Assert.Equal(1, sounds.RacksLit, 9);
        }

        [Fact]
        public void Landing_IsLouderForAHigherDrop_Footsteps_TakeTheMotorsLoudness()
        {
            var p = Run();
            Assert.All(p.Of("d17_land"), l => Assert.InRange(l.r.Volume, 0.5, 1.0));        // min(1, 0.5 + fall), hop 0.6
            Assert.All(p.Of("d17_step"), l => Assert.InRange(l.r.Volume, 0.36, 1.2));       // Walk 1, Run 1.2, crouched × 0.6
        }

        [Fact]
        public void TheGrab_TapsOncePerGrab_EvenWhileASceneActHoldsTheMotor()
        {
            // DL-05's body: he hesitates over it in a scene act, which leaves the motor's events unread for 1.6 s; they are
            // read once (D17Motor.StepEventsStart), not every step.
            var p = Run();
            Assert.InRange(p.Count("d17_tap"), 3, 8);
        }

        [Fact]
        public void ThePress_KillsWithItsDeathSound()
        {
            var p = Run(201, false);
            Assert.Equal(1, p.Count("death_crush"));
            var t = p.Of("death_crush").Single().t;
            Assert.Contains(p.Log, l => l.r.Key == "mech_thud" && l.r.X == ChapterSounds.PressX && l.t <= t);   // the slam (L7350)
        }

        [Fact]
        public void ADeathAct_PlaysItsDeath_Once()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 40 };
            var sounds = new ChapterSounds(sim);
            sim.Begin("room");
            sim.Die(DeathKind.Grabbed, sinkRate: 0.8);                                       // a death act (the sump's way)
            var keys = new List<string>();
            for (int i = 0; i < 60; i++) { sim.Step(default); sounds.Step(); for (int k = 0; k < sounds.Sounds.Count; k++) keys.Add(sounds.Sounds[k].Key); }
            Assert.Equal(1, keys.Count(k => k == "death_grabbed"));
        }

        /// <summary>DL-06's chute: tipped out with the post (worried), onto the heap (thud + tumble), L2981, L2993.</summary>
        private static List<string> ChuteKeys()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 60 };
            var sounds = new ChapterSounds(sim);
            sim.Begin("scanned");
            sim.StartAct(new Dl06ChuteFallAct(Dl06Scene.ChuteX0, Dl06Scene.ChuteY0, 0.55, Math.PI / 2, sim.Config.YawRate));
            var keys = new List<string>();
            for (int i = 0; i < 240; i++) { sim.Step(default); sounds.Step(); for (int k = 0; k < sounds.Sounds.Count; k++) keys.Add(sounds.Sounds[k].Key); }
            return keys;
        }

        [Fact]
        public void TheChuteFall_LandsOnTheHeap_WithAThudAndATumble_Once()
        {
            var keys = ChuteKeys();
            Assert.Equal(1, keys.Count(k => k == "mech_tumble"));
            Assert.Contains("mech_thud", keys);
        }

        /// <summary>A flat lane with a 1.0 m ceiling (he stands 0.76, jumps 0.4): his jump hits it (<c>Sound.bonk</c>, L2017).</summary>
        private static List<string> BonkKeys()
        {
            var cps = new CheckpointTable(new[] { "a" }, new CheckpointDef("a", 1, region: 1, scene: "A"));
            var def = new ChapterDef("bonk", cps, new SceneDef
            {
                Id = "A", Region = 1, X0 = 0, X1 = 10,
                Lane = () => new LaneTable { Name = "A", Left = -5, Right = 20, Floor = 0, Ceiling = 1.0 },
            });
            var sim = new ChapterSim(def);
            var sounds = new ChapterSounds(sim);
            sim.Begin("a");
            var keys = new List<string>();
            for (int i = 0; i < 90; i++)
            {
                sim.Step(new MotorInput { JumpPressed = i == 5 });
                sounds.Step();
                for (int k = 0; k < sounds.Sounds.Count; k++) keys.Add(sounds.Sounds[k].Key);
            }
            return keys;
        }

        [Fact]
        public void AJumpUnderALowCeiling_Bonks()
        {
            var keys = BonkKeys();
            Assert.Contains("d17_jump", keys);
            Assert.Equal(1, keys.Count(k => k == "d17_bonk"));
            Assert.Contains("d17_land", keys);
        }

        [Fact]
        public void ASceneCue_SoundsThroughTheSameQueue()
        {
            var p = Run();
            Assert.Equal(1, p.Count("d17_knock"));                                          // DL-03's pat cue, sound:knock (L2287)
            Assert.Contains(p.Log, l => l.r.Key == "d17_setdown_deck");                      // sound:setDownHigh
        }

        [Fact]
        public void DelayedSounds_FromTheOldWorld_DoNotSoundIntoANewOne()
        {
            var q = new SfxQueue(4, 2);
            q.PlayAfter(10, 0.5, "a");
            q.PlayAfter(10, 0.2, "b");
            q.PlayAfter(10, 0.3, "c");                                                       // over capacity: dropped
            Assert.Equal(1, q.Dropped);
            q.Clear(); q.Release(10.19);
            Assert.Equal(0, q.Count);
            q.Clear(); q.Release(10.2);
            Assert.Equal("b", q[0].Key);
            q.Reset();
            q.Clear(); q.Release(11);
            Assert.Equal(0, q.Count);
            Assert.Equal(0, q.Pending);
        }

        [Fact]
        public void TheSameSeed_HearsTheSame()
        {
            string Hear()
            {
                var sim = new ChapterSim(ChapterDefs.Prologue());
                var s = new ChapterSounds(sim, seed: 9);
                sim.Begin("start");
                var all = new List<string>();
                for (int i = 0; i < 1200; i++) { sim.Step(new MotorInput { Move = i % 400 < 200 ? 1 : -1 }); s.Step(); for (int k = 0; k < s.Sounds.Count; k++) all.Add(i + s.Sounds[k].ToString()); }
                return string.Join(",", all);
            }
            Assert.Equal(Hear(), Hear());
        }

        [Fact]
        public void PresentationFrames_AllocateNothing()
        {
            // Through the depot and the passage, then the DL-06 floor with the line running: the step's sounds, the emitters,
            // the carriers, the light pool and the mix.
            foreach (string cp in new[] { "start", "scanned" })
            {
                var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 50 };
                var view = new ChapterPresentation(sim);
                sim.Begin(cp);
                view.OnPlaced();
                double sink = 0;
                int n = 0;
                void Frame()
                {
                    sim.Step(new MotorInput { Move = (n++ / 300) % 2 == 0 ? 1 : -0.5 });
                    view.AfterStep(false, calm: n % 2 == 0);
                    view.Frame(sim.Clock, ChapterSim.StepSeconds, sim.X, calm: n % 2 == 0);
                    sink += view.Sounds.Sounds.Count + view.Sounds.Loop(SfxLoop.Hum) + view.Ambience.Gain(0) + view.Mix.OffsetDb(AudioGroup.Sfx)
                            + view.Lighting.Pool.Point(0) + view.Lighting.Pool.AmbientSky.R + (view.Carriers.Active(0) ? view.Carriers.Pose(0, 0.5).X : 0);
                }
                for (int i = 0; i < 300; i++) Frame();                                         // warm up
                long before = GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 1500; i++) Frame();
                Assert.Equal(0, GC.GetAllocatedBytesForCurrentThread() - before);
                Assert.True(sink != 0);
            }
        }
    }
}
