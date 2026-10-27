using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl07;
using DeadLetter.Core.Scenes.Dl08;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-08 as Core runs it in the prologue's chapter (<see cref="ChapterDefs.Prologue"/>), for what the golden trace does
    /// not play: the crates as a reload replays them, the pawl holding the platform whatever the pan, the shaft walled
    /// while the platform is down, the trolley's travel, careful by the sump, falling into the shaft, the respawn at
    /// <c>latched</c>. L1714–L1766, L1925, L2337–L2347, L3008–L3016, L3128–L3207, L3290–L3337, L3412–L3439, L4123,
    /// L7371–L7376, L8043–L8046.
    /// </summary>
    public class Dl08SceneSimTests
    {
        private static readonly MotorInput None = MotorInput.None;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };

        private static ChapterSim Begin(string cp)
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 300 };
            s.Begin(cp);
            return s;
        }

        private static Handbrake08 Rules(ChapterSim s) => (Handbrake08)s.RulesOf(s.Def.Scene(Dl08Scene.Id));

        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 6000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " y=" + s.Y + " act=" + SceneSim.KindOf(s) + " scene=" + s.Current?.Id);
        }

        /// <summary>The belt's crates as text: count, then each crate's type, state, x, y, z, t and spin (R format).</summary>
        private static string Crates(ReturnsBelt b)
        {
            var sb = new StringBuilder().Append(b.State).Append(' ').Append(b.Next.ToString("R", CultureInfo.InvariantCulture)).Append(' ').Append(b.Count);
            for (int i = 0; i < b.Count; i++)
            {
                var c = b.At(i);
                sb.Append(" [").Append(c.Type).Append(' ').Append(c.State).Append(' ').Append(c.X.ToString("R", CultureInfo.InvariantCulture))
                  .Append(' ').Append(c.Y.ToString("R", CultureInfo.InvariantCulture)).Append(' ').Append(c.Z.ToString("R", CultureInfo.InvariantCulture))
                  .Append(' ').Append(c.T.ToString("R", CultureInfo.InvariantCulture)).Append(' ').Append(c.Spin.ToString("R", CultureInfo.InvariantCulture)).Append(']');
            }
            return sb.ToString();
        }

        private static List<string> Run(ChapterSim s, int steps)
        {
            var b = Rules(s).Belt;
            var log = new List<string>(steps);
            for (int i = 0; i < steps; i++) { s.Step(None); log.Add(Crates(b)); }
            return log;
        }

        // ---- The returns belt -----------------------------------------------------------------------------------------
        /// <summary>
        /// At <c>latched</c> he stands past the shaft with the pawl set: the warning (bells at 0, 0.9, 1.8 s), the klaxon at
        /// 2.7 s, then crates down the chute onto the belt toward him at 0.32 m/s. A respawn there (the whole world reloaded,
        /// the belt's generator reseeded) replays the same crates on the same steps, bit for bit; so does the world restored
        /// from a snapshot taken mid-run (the generator is in the snapshot).
        /// </summary>
        [Fact]
        public void Crates_Spawn_AndReplayIdentically_AfterARespawn_AndFromASnapshot_L3128_L3169_L8045()
        {
            var s = Begin(Dl08Scene.LatchedCheckpoint);
            var b = Rules(s).Belt;
            Assert.Equal(ReturnsBeltState.Idle, b.State);
            var first = Run(s, 2400);                                                       // 40 s
            Assert.StartsWith("Warn", first[0]);                                            // free, grounded, past SHAFT.x1 + 0.6 (L3420)
            int spawned = 0, prev = 0;
            foreach (var l in first)
            {
                int n = int.Parse(l.Split(' ')[2], CultureInfo.InvariantCulture);
                if (n > prev) spawned += n - prev;
                prev = n;
            }
            Assert.InRange(spawned, 6, 10);                                                  // every 2.9–4.2 s, 1.25 behind the last (L3141–L3144)
            Assert.Equal(ReturnsBeltState.Run, b.State);

            s.Respawn();                                                                    // the checkpoint is still latched
            Assert.Equal(ReturnsBeltState.Idle, b.State);
            Assert.Equal(0, b.Count);
            Assert.Equal(first, Run(s, 2400));

            // A snapshot mid-run: the rest of the run again from it.
            s.Respawn();
            Run(s, 1000);
            var snap = Mech.Snapshot(s.Graph);
            var rest = Run(s, 1400);
            s.Graph.Restore(snap);
            Assert.Equal(rest, Run(s, 1400));
        }

        /// <summary>Riding the belt he is carried back toward the landing while he stands on it (<c>beltCarry4</c>, L3439).</summary>
        [Fact]
        public void Belt_CarriesHimBack_WhileItRuns_L3439()
        {
            var s = Begin(Dl08Scene.LatchedCheckpoint);
            var b = Rules(s).Belt;
            Until(s, None, x => b.State == ReturnsBeltState.Run);
            s.Motor.Place(93.0, Dl08Lane.Deck);
            for (int i = 0; i < 60; i++) s.Step(None);
            Assert.InRange(s.X, 93.0 - 0.32 - 1e-9, 93.0 - 0.32 + 1e-9);
        }

        // ---- The platform and the pawl ----------------------------------------------------------------------------------
        /// <summary>
        /// The trolley on the pan winds the platform up to the landing; the pawl, pulled there, bites (LeverPull, f22) and
        /// Proud follows; then with the trolley rolled back off the pan the platform stays at the landing, and he walks onto it
        /// without a teeter. Unlatched, the same step onto it drops it under him (Teeter) and he scrambles back.
        /// </summary>
        [Fact]
        public void Pawl_HoldsThePlatform_AtTheLanding_WhateverThePan_L3182_L3290_L3324()
        {
            var s = Begin(Dl08Scene.GoodsCheckpoint);
            var r = Rules(s);
            Assert.Equal(0, r.Platform.H);
            Assert.Equal(Dl08Lane.Deck, s.Y);                                                 // goods: on the deck (c.upper, L8039)
            r.Trolley.MoveTo(r.Trolley.Max, 0); r.Trolley.OnReleased(false);                 // the trolley on the pan, against its buffer
            Until(s, None, x => r.Platform.H >= 0.985);
            Until(s, None, x => r.Platform.State == CounterweightLiftState.Still);

            s.Motor.Place(85.45, Dl08Lane.Deck);
            s.Step(Use);
            Until(s, None, x => r.Pawl.Engaged);
            Until(s, None, x => SceneSim.KindOf(x) == "quirk");                                // Proud after he steps back (L3299)
            Assert.Equal("Proud", SceneSim.PhaseOf(s));

            r.Trolley.MoveTo(82.5, 0); r.Trolley.OnReleased(false);                           // the pan empty
            for (int i = 0; i < 300; i++) s.Step(None);
            Assert.Equal(0, r.Pan.Load);
            Assert.Equal(1.0, r.Platform.H, 9);                                               // within the 1e-4 dead band (L3184)
            Assert.True(r.Platform.Latched);
            s.Motor.Place(85.6, Dl08Lane.Deck);
            Until(s, Right, x => x.X > 87.0, 400);
            Assert.Null(SceneSim.KindOf(s));
            Assert.Equal(Dl08Lane.Deck, s.Y, 9);

            var u = Begin(Dl08Scene.GoodsCheckpoint);                                          // unlatched, at the landing
            var ru = Rules(u);
            ru.Trolley.MoveTo(ru.Trolley.Max, 0); ru.Trolley.OnReleased(false);
            Until(u, None, x => ru.Platform.H >= 1 - 1e-4);
            u.Motor.Place(85.6, Dl08Lane.Deck);
            Until(u, Right, x => SceneSim.KindOf(x) == "dl08.platform", 200);
            Assert.True(ru.Platform.Lurching);
            Until(u, None, x => x.Act == null, 200);
            Assert.Equal(Dl08Lane.ShaftX0 - 0.28, u.X, 9);                                    // back 0.28 outside the edge (L3279)
            Assert.Equal(Dl08Lane.Deck, u.Y);
            Assert.False(ru.Platform.Lurching);
        }

        /// <summary>With the platform down and unlatched the shaft's edge walls him (<c>rightLimit0</c>, L1766).</summary>
        [Fact]
        public void Shaft_WallsHim_WhileThePlatformIsDown_L1755_L1766()
        {
            var s = Begin(Dl08Scene.GoodsCheckpoint);
            s.Motor.Place(85.0, Dl08Lane.Deck);
            for (int i = 0; i < 120; i++) s.Step(Right);
            Assert.Equal(Dl08Lane.ShaftX0 - Dl08Lane.Half + 0.08, s.X, 9);
            Assert.Equal(Dl08Lane.Deck, s.Y);
        }

        /// <summary>The trolley stops at the pan's buffer until the pawl is set, then on across the platform at the rail (L2340, L4123).</summary>
        [Fact]
        public void Trolley_StopsAtThePansBuffer_UntilThePawlIsSet_ThenAtTheRail_L2340()
        {
            var g = Rules(Begin(Dl08Scene.GoodsCheckpoint)).Trolley;
            Assert.Equal(82.5, g.X, 9);
            Assert.Equal(84.5, g.Max, 9);
            var l = Rules(Begin(Dl08Scene.LatchedCheckpoint)).Trolley;
            Assert.Equal(88.22, l.X, 9);
            Assert.Equal(88.22, l.Max, 9);
        }

        // ---- The sump --------------------------------------------------------------------------------------------------
        /// <summary>Within 2 m of the sump's water, auto-run walks (<c>wantsRun</c>, L1925); outside it runs.</summary>
        [Theory]
        [InlineData(84.0, true)]
        [InlineData(90.2, true)]
        [InlineData(82.0, false)]
        [InlineData(93.0, false)]
        public void Careful_ByTheSump_L1925(double x, bool careful)
        {
            var s = Begin(Dl08Scene.LatchedCheckpoint);
            s.Motor.Place(x, Dl08Lane.Deck);
            s.Step(None);
            Assert.Equal(careful, s.Motor.Careful);
        }

        /// <summary>Down in the shaft's water he is dragged under (grabbed, sinking 0.8 m/s, 1.3 s to the cut), and respawns at the checkpoint.</summary>
        [Fact]
        public void Sump_FallingIn_IsADeath_ThenTheRespawn_L7373_L7375()
        {
            var s = Begin(Dl08Scene.GoodsCheckpoint);
            s.Motor.Place(87.0, -0.3);
            s.Step(None);
            var d = Assert.IsType<DeathAct>(s.Act);
            Assert.Equal(Hazards.DeathKind.Grabbed, d.Profile.Kind);
            Assert.Equal(1.3, d.Profile.Hold);
            double y = s.Y;
            s.Step(None);
            Assert.Equal(y - 0.8 / 60, s.Y, 12);
            Until(s, None, x => x.Act == null && x.X < 82, 200);
            Assert.Equal(Dl08Scene.GoodsCheckpoint, s.Checkpoints.Current.Name);
            Assert.Equal(1, s.Deaths);
        }

        // ---- Checkpoints ---------------------------------------------------------------------------------------------
        /// <summary>
        /// <c>latched</c> is reached past the shaft with the pawl set (L3419), and a respawn there (the world as it was when he
        /// reached it) puts him in DL-08, region 4, on the far landing's deck (89.2, 1.6), with the pawl set, the platform at
        /// the landing, the belt still, the gallery collapsed behind him and him still up (<c>c.upper</c>). Beginning there (a
        /// continue) builds the same world, with the trolley parked by the rail (L4123).
        /// </summary>
        [Fact]
        public void Respawn_AtLatched_LandsInDl08_L3419_L8015_L8046()
        {
            var s = Begin(Dl08Scene.GoodsCheckpoint);
            var r = Rules(s);
            Assert.Equal(Dl08Scene.Id, s.Current.Id);
            r.Trolley.MoveTo(r.Trolley.Max, 0); r.Trolley.OnReleased(false);
            Until(s, None, x => r.Platform.H >= 0.985);
            s.Motor.Place(85.45, Dl08Lane.Deck);
            s.Step(Use);
            Until(s, None, x => r.Pawl.Engaged);
            Until(s, None, x => x.Act == null && !x.Motor.IsActing);
            s.Motor.Place(88.85, Dl08Lane.Deck);                                               // past SHAFT.x1 + 0.35, short of the belt's trigger (L3419, L3420)
            s.Step(None);
            Assert.Equal(Dl08Scene.LatchedCheckpoint, s.Checkpoints.Current.Name);
            Assert.Equal(ReturnsBeltState.Idle, r.Belt.State);
            s.Motor.Place(89.0, Dl08Lane.Deck);
            Until(s, None, x => r.Belt.State == ReturnsBeltState.Run);
            s.Motor.Place(93.0, Dl08Lane.Deck);

            s.Respawn();
            Assert.Equal(Dl08Scene.Id, s.Current.Id);
            Assert.Equal(4, s.Region);
            Assert.Equal(33 + 56.2, s.X, 12);
            Assert.Equal(Dl08Lane.Deck, s.Y);
            Assert.True(s.Grounded);
            Assert.True(r.Pawl.Engaged);
            Assert.Equal(1.0, r.Platform.H, 9);
            Assert.Equal(ReturnsBeltState.Idle, r.Belt.State);
            Assert.True(s.Graph.Get<Dl07Gallery>("dl07.gallery").Upper);
            Assert.Equal(CollapseState.Gone, s.Graph.Get<Dl07Collapse>("dl07.collapse").State);
            s.Step(None);
            Assert.Equal(Dl08Lane.Deck, s.Y);
            Assert.Equal(ReturnsBeltState.Warn, r.Belt.State);                                 // he stands past SHAFT.x1 + 0.6

            var c = Begin(Dl08Scene.LatchedCheckpoint);
            var rc = Rules(c);
            Assert.Equal(Dl08Scene.Id, c.Current.Id);
            Assert.True(rc.Pawl.Engaged);
            Assert.Equal(1.0, rc.Platform.H);
            Assert.Equal(88.22, rc.Trolley.X, 9);
            Assert.Equal(33 + 56.2, c.X, 12);
            Assert.Equal(Dl08Lane.Deck, c.Y);
        }

        /// <summary>Walking left out of the doorway he is in region 3 again (L2045), on DL-07's gallery.</summary>
        [Fact]
        public void BackThroughTheDoorway_IsRegion3_L2045()
        {
            var s = Begin(Dl08Scene.GoodsCheckpoint);
            Until(s, new MotorInput { Move = -1 }, x => x.Region == 3, 600);
            Assert.True(s.X < Dl08Lane.Region4X - 0.2);
            Assert.Equal(Dl07Scene.Id, s.Current.Id);
        }
    }
}
