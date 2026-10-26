using System;
using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Mechanisms;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>The White on its own (§4.15; L7040–L7198, L7234–L7273, L7326–L7330), driven by a scripted hero.</summary>
    public class WhiteTests
    {
        private const double Dt = Mech.Dt;
        private const string Id = "dl11.white";

        /// <summary>The lane without its positional first sighting, so he can stand on the edge from the start.</summary>
        private static WhiteParams QuietLane()
        {
            var lane = WaterBody.Lane9();
            lane.ShowWhenHeroPastX = double.NaN;
            return new WhiteParams { Waters = new[] { lane } };
        }

        private sealed class Rig
        {
            public readonly BeingSenses S = new BeingSenses { Region = 5 };
            public readonly WhiteBrain W;
            public readonly MechanismGraph G;
            public double X = 140, Y;
            public readonly List<MechanismEvent> Log = new List<MechanismEvent>();

            public Rig(WhiteParams p = null, string cp = "ringc", int region = 5)
            {
                S.Region = region;
                W = new WhiteBrain(Id, p ?? WhiteParams.Dl11(), S);
                G = Mech.Graph(cp, W);
            }

            public void Step(params NoiseEvent[] posts)
            {
                S.BeginStep();
                foreach (var n in posts) S.Noises.Post(n);
                G.Step(Dt, Mech.Pose(X, Y));
                Log.AddRange(Mech.Events(G));
            }

            public void Run(int steps) { for (int i = 0; i < steps; i++) Step(); }

            /// <summary>Steps until the condition holds after a step; returns the steps taken (or -1).</summary>
            public int Until(Func<bool> cond, int max = 5000)
            {
                for (int i = 1; i <= max; i++) { Step(); if (cond()) return i; }
                return -1;
            }

            public bool Entered(WhiteState s) => Mech.Entered(G, Id, s);
            public bool Emitted(WhiteEvent e) => Mech.Emitted(G, Id, e);
            public int Count(WhiteEvent e) => Log.FindAll(x => x.Kind == MechanismEventKind.Event && x.Code == (int)e).Count;
        }

        private static string NoTick(MechanismGraph g)
        {
            var lines = new List<string>(Mech.Dump(g).Split('\n'));
            lines.RemoveAll(l => l.StartsWith("graph/tick=", StringComparison.Ordinal));
            return string.Join("\n", lines);
        }

        // ---- Water selection ----------------------------------------------------------------------------------------

        [Fact]
        public void Water_IsTheFirstActiveOneOfHisRegion_AndItStartsPatrollingFromTheCentre_L7107_L7111()
        {
            var r = new Rig(WhiteParams.Chapter1(), region: 5);
            Assert.Equal(WhiteState.Away, r.W.State);                          // after Reset, before a step
            r.Step();
            Assert.True(r.Entered(WhiteState.Patrol));
            Assert.Equal("lane9", r.W.Water.Id);
            Assert.InRange(r.W.X, 148.275 - 0.25 * Dt - 1e-9, 148.275);       // the centre, then one glide step
            r.X = 153.6; r.Step();                                             // past the lane's active range (L7239)
            Assert.Equal(WhiteState.Away, r.W.State);
            Assert.Null(r.W.Water);

            r.S.Region = 4; r.X = 87; r.Step();
            Assert.Equal("sump7", r.W.Water.Id);
            r.X = 91.3; r.Step();                                              // active while x < 88.3 + 3 (L7329)
            Assert.Null(r.W.Water);

            r.S.Region = 3; r.X = 70; r.S.Upper = true; r.Step();
            Assert.Null(r.W.Water);                                            // the heap is below the gallery (L7327)
            r.S.Upper = false; r.Step();
            Assert.Equal("heap", r.W.Water.Id);
        }

        [Fact]
        public void Patrol_GlidesAt025_AndRetargetsAfterSixSeconds_InsideTheWater_FromItsOwnSeed_L7136()
        {
            var a = new Rig();
            a.Step();
            double x0 = a.W.X;
            a.Step();
            Assert.Equal(0.25 * Dt, x0 - a.W.X, 12);                           // toward its initial target, x 0
            Assert.Equal(0, a.W.TargetX);
            int k = a.Until(() => a.W.TargetX != 0, 400);
            Assert.InRange(k, 358, 360);                                       // t > 6 s since it began patrolling
            Assert.InRange(a.W.TargetX, 145.95 + 0.4, 150.6 - 0.4);

            var b = new Rig();
            b.Run(k + 2);
            Assert.Equal(a.W.TargetX, b.W.TargetX);                            // same seed, same target
            var p = WhiteParams.Dl11(); p.Seed = 12345;
            var c = new Rig(p);
            c.Run(k + 2);
            Assert.NotEqual(a.W.TargetX, c.W.TargetX);
        }

        [Fact]
        public void Body_StaysInsideTheWater_SnoutLeading_L7183_L7186()
        {
            // Lured past either end: the snout stops 0.15 inside the water ahead of it.
            var r = new Rig(QuietLane());
            r.Step(); r.Step(NoiseEvent.Lure(140, 30, 1));
            r.Run(400);
            Assert.Equal(-1, r.W.Facing);
            Assert.Equal(145.95 + 0.15, r.W.X, 12);
            r.Step(NoiseEvent.Lure(160, 30, -1));
            r.Run(400);
            Assert.Equal(1, r.W.Facing);
            Assert.Equal(150.6 - 0.15, r.W.X, 12);
            // Facing +x, the tail (2.5·0.8 = 2 m) trails behind the snout: put there by a sighting, it is pulled in.
            var lane = WaterBody.Lane9(); lane.ShowWhenHeroPastX = double.NaN; lane.ShowX = 146.2;
            var t = new Rig(new WhiteParams { Waters = new[] { lane } });
            t.Step(); t.Step(NoiseEvent.Lure(160, 30, -1)); t.Run(5);
            Assert.Equal(1, t.W.Facing);
            t.Step(NoiseEvent.Scare(30)); t.Step(NoiseEvent.Show("lane9"));
            Assert.Equal(145.95 + 2.0, t.W.X, 12);
        }

        // ---- Hearing ------------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(144.6, 1.3, true, true)]      // running within 1.4 m of the water
        [InlineData(144.6, -1.3, true, true)]     // either way
        [InlineData(144.6, 1.2, true, false)]     // walking speed: quiet
        [InlineData(144.5, 1.3, true, false)]     // 1.45 m away
        [InlineData(152.0, 1.6, true, false)]     // 1.4 m past the far end (exclusive)
        [InlineData(151.9, 1.6, true, true)]
        [InlineData(146.0, 1.6, false, false)]    // in the air
        public void RunningNearTheWater_IsLoud_WalkingIsNot_L7119_L7120(double x, double vx, bool grounded, bool heard)
        {
            var r = new Rig(QuietLane()) { X = x };
            r.S.Vx = vx; r.S.Grounded = grounded;
            r.Step();
            Assert.Equal(heard, r.Emitted(WhiteEvent.Heard));
            Assert.Equal(heard ? WhiteState.Listen : WhiteState.Patrol, r.W.State);   // the patrol hears it at once (L7138)
        }

        [Fact]
        public void RunningNoise_HasA035sCooldown_L7120()
        {
            var r = new Rig(QuietLane()) { X = 146 };
            r.S.Vx = 1.6;
            var at = new List<int>();
            for (int i = 0; i < 120; i++) { r.Step(); if (r.Emitted(WhiteEvent.Heard)) at.Add(i); }
            Assert.True(at.Count >= 5);
            for (int i = 1; i < at.Count; i++) Assert.InRange(at[i] - at[i - 1], 21, 22);
        }

        [Fact]
        public void NotInPlay_HeIsNeitherHeardNorExposed_L7117_L7149()
        {
            var r = new Rig(QuietLane()) { X = 147 };
            r.S.Alive = false; r.S.Vx = 1.6;
            r.Run(60);
            Assert.Equal(0, r.Count(WhiteEvent.Heard));
            r.Step(NoiseEvent.Sound(147, 1, 5));
            Assert.True(r.Until(() => r.W.State == WhiteState.Approach, 60) > 0);
            Assert.True(r.Until(() => r.W.State == WhiteState.Surface, 300) > 0);
            Assert.True(r.Until(() => r.W.State == WhiteState.Sink, 300) > 0);
            Assert.Equal(0, r.Count(WhiteEvent.Warn));
            Assert.Equal(0, r.Count(WhiteEvent.Grab));
        }

        [Theory]
        [InlineData(145.95 - 2.49, 1.0, 5, true)]
        [InlineData(145.95 - 2.51, 1.0, 5, false)]
        [InlineData(150.6 + 3.74, 1.5, 5, true)]    // a splash carries 2.5·1.5
        [InlineData(150.6 + 3.76, 1.5, 5, false)]
        [InlineData(148.0, 1.0, 4, false)]          // another region's sound
        public void Hearing_ReachesTwoAndAHalfLoudPastTheWater_InItsRegion_L7097_L7099(double x, double loud, int region, bool heard)
        {
            var r = new Rig(QuietLane());
            r.Step();
            r.Step(NoiseEvent.Sound(x, loud, region));
            Assert.Equal(heard, r.Emitted(WhiteEvent.Heard));
            if (heard) Assert.InRange(r.W.HeardX, 145.95 + 0.3, 150.6 - 0.3);          // clamped 0.3 inside (L7101)
        }

        // ---- Listen, approach, surface ------------------------------------------------------------------------------

        [Theory]
        [InlineData(false, 42, 43)]   // 0.7 s
        [InlineData(true, 18, 19)]    // glimpse water: 0.3 s
        public void Listen_ThenApproach_L7139_L7141(bool glimpse, int min, int max)
        {
            var r = glimpse ? new Rig(WhiteParams.Chapter1(), region: 3) { X = 69 } : new Rig(QuietLane());
            r.Step();
            r.Step(NoiseEvent.Sound(glimpse ? 70.5 : 149, 1, glimpse ? 3 : 5));
            Assert.True(r.Entered(WhiteState.Listen));
            Assert.InRange(r.Until(() => r.W.State == WhiteState.Approach, 100), min, max);
        }

        [Fact]
        public void Approach_SwimsAt125_ToWhereItHeard_WithRipples_ThenSurfaces_L7142_L7145_L7215()
        {
            var r = new Rig(QuietLane()) { X = 140 };
            r.Step();
            r.Step(NoiseEvent.Sound(150.0, 1, 5));
            r.Until(() => r.W.State == WhiteState.Approach, 100);
            var ripples = new List<long>();
            double prev = r.W.X;
            int n = 0;
            while (r.W.State == WhiteState.Approach && n++ < 600)
            {
                r.Step();
                if (r.W.State == WhiteState.Approach) Assert.Equal(1.25 * Dt, r.W.X - prev, 9);
                prev = r.W.X;
                foreach (var e in Mech.Events(r.G))
                    if (e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Ripple)
                    {
                        ripples.Add(e.Tick);
                        Assert.Equal(r.W.X - 1.25 * Dt + 0.4, e.Value, 9);           // 0.4 ahead of the snout, before it moved
                    }
            }
            Assert.Equal(WhiteState.Surface, r.W.State);
            Assert.InRange(Math.Abs(r.W.X - 150.0), 0, 0.2);
            Assert.Equal(1, r.W.Facing);
            Assert.True(ripples.Count >= 3);
            for (int i = 1; i < ripples.Count; i++) Assert.InRange(ripples[i] - ripples[i - 1], 11, 12);   // ≥ 0.18 s apart
        }

        [Fact]
        public void Surface_TimesOutAfter22s_ThenSinks12s_AndForgets_L7154_L7177()
        {
            var r = new Rig(QuietLane()) { X = 140 };                           // not on the edge: never exposed
            r.Step();
            r.Step(NoiseEvent.Sound(148, 1, 5));
            r.Until(() => r.W.State == WhiteState.Surface, 400);
            r.Step();
            Assert.Equal(WhiteClip.Surface, r.W.Clip);                         // set from its first surfaced step
            Assert.InRange(r.Until(() => r.W.State == WhiteState.Sink, 400), 131, 132);
            Assert.True(r.W.HasHeard);
            Assert.InRange(r.Until(() => r.W.State == WhiteState.Patrol, 400), 72, 73);
            Assert.False(r.W.HasHeard);
        }

        /// <summary>Drive it to surface right beside him on the edge at <paramref name="x"/>.</summary>
        private static Rig SurfaceBeside(WhiteParams p, int region, double x, double noiseX)
        {
            var r = new Rig(p, region: region) { X = x };
            r.Step();
            r.Step(NoiseEvent.Sound(noiseX, 1, region));
            Assert.True(r.Until(() => r.W.State != WhiteState.Patrol && r.W.State != WhiteState.Listen && r.W.State != WhiteState.Approach
                && r.W.State != WhiteState.Surface, 800) > 0);
            return r;
        }

        [Fact]
        public void HuntWater_FirstFind_WarnsAndSinks_ThenStrikes_GrabbingAt056s_L7150_L7161()
        {
            var r = SurfaceBeside(QuietLane(), 5, 147.5, 147.5);
            Assert.True(r.Entered(WhiteState.Sink));                           // straight past Surface: same step
            Assert.True(r.Emitted(WhiteEvent.Warn));
            Assert.True(r.W.Warned);
            Assert.Equal(0, r.Count(WhiteEvent.Grab));

            r.Until(() => r.W.State == WhiteState.Patrol, 200);
            r.Step(NoiseEvent.Sound(147.5, 1, 5));
            double before = r.W.X;
            Assert.True(r.Until(() => { if (r.W.State != WhiteState.Strike) before = r.W.X; return r.W.State == WhiteState.Strike; }, 800) > 0);
            Assert.Equal(r.X - before >= 0 ? 1 : -1, r.W.Facing);              // it faces him from where it surfaced (L7153)
            int grab = r.Until(() => r.Emitted(WhiteEvent.Grab), 100);
            Assert.InRange(grab, 34, 34);                                     // t > 0.56: the jaws close at frame 14
            Assert.Equal(WhiteClip.Lunge, r.W.Clip);
            Assert.Equal(0.08, r.W.ClipFade);
            var e = Mech.Events(r.G).Find(x => x.Code == (int)WhiteEvent.Grab && x.Kind == MechanismEventKind.Event);
            Assert.Equal(1.6, e.Value);                                       // die('grabbed', {hold: 1.6})
            r.S.Alive = false;                                                 // the death act
            Assert.InRange(r.Until(() => r.Emitted(WhiteEvent.Drag), 100), 15, 16);   // 0.25 s later it drags him under
            Assert.Equal(WhiteClip.Drag, r.W.Clip);
            Assert.InRange(r.Until(() => r.W.State == WhiteState.Sink, 200), 144 - 34 - 16, 145 - 34 - 15);   // gives up at 2.4 s
            Assert.Equal(1, r.Count(WhiteEvent.Grab));
            Assert.Equal(1, r.Count(WhiteEvent.Warn));
        }

        [Fact]
        public void ScareWater_SlapsHimBack_At035s_Unhurt_ThenSinksAt13s_L7156_L7159()
        {
            var r = SurfaceBeside(WhiteParams.Chapter1(), 4, 86.0, 86.2);
            Assert.True(r.Entered(WhiteState.Slap));
            int slap = r.Until(() => r.Emitted(WhiteEvent.Slap), 100);
            Assert.InRange(slap, 21, 22);
            Assert.Equal(WhiteClip.Slap, r.W.Clip);
            Assert.Equal(0.1, r.W.ClipFade);
            var e = Mech.Events(r.G).Find(x => x.Code == (int)WhiteEvent.Slap && x.Kind == MechanismEventKind.Event);
            Assert.Equal(Math.Sign(86.0 - r.W.X) == 0 ? -1 : Math.Sign(86.0 - r.W.X), e.Index);   // knocked away from it
            Assert.InRange(r.Until(() => r.W.State == WhiteState.Sink, 200), 78 - slap - 1, 79 - slap);
            Assert.Equal(1, r.Count(WhiteEvent.Slap));
            Assert.Equal(0, r.Count(WhiteEvent.Grab));
            Assert.Equal(0, r.Count(WhiteEvent.Warn));
            Assert.False(r.W.Warned);                                          // only hunt water warns
        }

        [Fact]
        public void GlimpseWater_OnlyRolls_EvenWithHimInIt_AndSinksAfter16s_L7147_L7154()
        {
            var r = new Rig(WhiteParams.Chapter1(), region: 3) { X = 69 };
            r.Step();
            r.Step(NoiseEvent.Sound(70.6, 1.5, 3));
            r.Until(() => r.W.State == WhiteState.Surface, 400);
            r.X = r.W.X + 0.3; r.Y = -0.8;                                      // in the water, under its nose
            r.Step();
            Assert.Equal(WhiteClip.Roll, r.W.Clip);
            int k = r.Until(() => r.W.State != WhiteState.Surface, 400);
            Assert.Equal(WhiteState.Sink, r.W.State);
            Assert.InRange(k, 95, 96);
            Assert.Equal(0, r.Count(WhiteEvent.Slap) + r.Count(WhiteEvent.Grab) + r.Count(WhiteEvent.Warn));
        }

        // ---- Lure and flee ------------------------------------------------------------------------------------------

        [Fact]
        public void Bell_LuresItToNoseAtTheStep_For12s_ThenItSinks_L7128_L7130_L7241()
        {
            var r = new Rig(QuietLane()) { X = 140 };
            r.Step();
            r.S.BeginStep(); Lane9Cues.RingBell(r.S.Noises);
            r.G.Step(Dt, Mech.Pose(r.X, r.Y));
            Assert.True(r.Entered(WhiteState.Lured));
            Assert.True(r.Emitted(WhiteEvent.Heard));
            Assert.Equal(146.4 + 0.5, r.W.TargetX, 12);                        // its nose 0.5 ahead, from the right
            r.Until(() => r.W.Clip == WhiteClip.Nose, 600);
            Assert.InRange(Math.Abs(r.W.X - 146.9), 0, 0.15);
            Assert.Equal(-1, r.W.Facing);
            r.Step(NoiseEvent.Sound(147, 0.5, 5));                             // a bell drowns out a footstep
            Assert.False(r.Emitted(WhiteEvent.Heard));
            int left = r.Until(() => r.W.State != WhiteState.Lured, 800);
            Assert.Equal(WhiteState.Sink, r.W.State);
            Assert.InRange(r.W.Clock, 12 + 2 * Dt - 1e-9, 12 + 3 * Dt + 1e-9); // rung at step 2 (clock 2·dt), 12 s
            Assert.True(left > 0);
        }

        [Theory]
        [InlineData(146.5, true)]     // running within 2.2 m of it breaks the lure
        [InlineData(144.6, false)]    // heard, but 2.3 m off: the bell holds it
        public void Bell_RunningNearby_BreaksTheLure_L7132(double x, bool breaks)
        {
            var r = new Rig(QuietLane()) { X = 140 };
            r.Step();
            r.S.BeginStep(); Lane9Cues.RingBell(r.S.Noises);
            r.G.Step(Dt, Mech.Pose(r.X, r.Y));
            r.Until(() => r.W.Clip == WhiteClip.Nose, 600);
            r.X = x; r.S.Vx = 1.6;
            r.Run(30);
            Assert.True(r.Count(WhiteEvent.Heard) >= 2);
            Assert.Equal(breaks, r.W.State != WhiteState.Lured);
            if (breaks) { Assert.False(r.W.Lured); Assert.True(r.Log.Exists(e => e.Kind == MechanismEventKind.State && e.Code == (int)WhiteState.Approach)); }
        }

        [Fact]
        public void Junction_ScaresItAway_For20s_DeafToEverything_L7106_L7125_L7250()
        {
            var r = new Rig(QuietLane()) { X = 147 };
            r.Step();
            r.S.BeginStep(); Lane9Cues.ThrowJunction(r.S.Noises);
            r.G.Step(Dt, Mech.Pose(r.X, r.Y));
            Assert.True(r.Entered(WhiteState.Flee));
            Assert.True(r.W.Fleeing);
            double x = r.W.X;
            r.S.Vx = 1.6;                                                      // he runs on the edge
            r.Step(NoiseEvent.Sound(147, 1.5, 5));
            Assert.Equal(0, r.Count(WhiteEvent.Heard));
            Assert.Equal(x, r.W.X);                                            // it holds where it is, going deep
            int k = r.Until(() => r.W.State != WhiteState.Flee, 1500);
            Assert.InRange(k, 1197, 1201);
            Assert.Equal(WhiteState.Patrol, r.W.State);
            Assert.DoesNotContain(r.Log, e => e.Kind == MechanismEventKind.State && e.Code == (int)WhiteState.Listen);
            Assert.True(r.W.Y < -0.1 - 1.0);                                   // it went deep (1.2 under)
        }

        // ---- First sightings ----------------------------------------------------------------------------------------

        [Fact]
        public void Lane_ShowsItselfFarOff_TheFirstTimeHeComesAlong_OncePerReset_L7271_L7272()
        {
            var r = new Rig() { X = 145.0 };
            r.Step();
            Assert.Equal(WhiteState.Patrol, r.W.State);
            r.X = 145.31; r.Step();
            Assert.True(r.Entered(WhiteState.Surface));
            Assert.True(r.Emitted(WhiteEvent.Shown));
            Assert.InRange(r.W.X, 150.6 - 2.0 - 1e-9, 149.9 + 1e-9);           // at 149.9, unless facing −x (tail in)
            r.Until(() => r.W.State == WhiteState.Patrol, 400);
            r.Run(10);
            Assert.Equal(1, r.Count(WhiteEvent.Shown));
            r.G.Reset(Mech.Cp("ringc"));
            r.Step(); r.Step();
            Assert.Equal(2, r.Count(WhiteEvent.Shown));
        }

        [Fact]
        public void Sump_ShowCue_SurfacesItAt8705_OnlyInThatWater_L7372()
        {
            var r = new Rig(WhiteParams.Chapter1(), region: 4) { X = 84 };
            r.Step(NoiseEvent.Show("sump7"));                                  // before it is in the sump: ignored
            r.Step(NoiseEvent.Show("lane9"));
            Assert.Equal(WhiteState.Patrol, r.W.State);
            r.Step(NoiseEvent.Show("sump7"));
            Assert.True(r.Entered(WhiteState.Surface));
            Assert.InRange(r.W.X, 88.3 - 2.5 * 0.55 - 1e-9, 87.05 + 1e-9);
        }

        [Fact]
        public void WantsCareful_Within2mOfScareOrHuntWater_NotGlimpse_L1925()
        {
            var r = new Rig(WhiteParams.Chapter1()) { X = 140 };
            r.Step();
            Assert.False(r.W.WantsCareful(143.9));
            Assert.True(r.W.WantsCareful(144.0));
            Assert.True(r.W.WantsCareful(152.5));
            Assert.False(r.W.WantsCareful(152.6));
            var heap = new Rig(WhiteParams.Chapter1(), region: 3) { X = 70 };
            heap.Step();
            Assert.False(heap.W.WantsCareful(70));
        }

        // ---- Reset, snapshot, determinism ---------------------------------------------------------------------------

        [Theory]
        [InlineData("ringc")]
        [InlineData("bedroom")]
        [InlineData("start")]
        public void Reset_RebuildsItAway_KeepingOnlyTheWarning_L4110_L7150(string cp)
        {
            var r = SurfaceBeside(QuietLane(), 5, 147.5, 147.5);
            Assert.True(r.W.Warned);
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(WhiteState.Away, r.W.State);
            Assert.Null(r.W.Water);
            Assert.False(r.W.HasHeard);
            Assert.False(r.W.Lured);
            Assert.False(r.W.Fleeing);
            Assert.Equal(0, r.W.Clock);
            Assert.True(r.W.Warned);                                           // persist.warned outlives a respawn
            r.W.NewGame();
            Assert.False(r.W.Warned);

            var fresh = new Rig(QuietLane(), cp) { X = 147.5 };
            r.Run(50); fresh.Run(50);
            Assert.Equal(NoTick(fresh.G), NoTick(r.G));
        }

        [Fact]
        public void SnapshotMidHunt_RestoresAndContinuesBitIdentically()
        {
            var a = new Rig(QuietLane()) { X = 147.5 };
            a.W.Warned = true;
            a.Step();
            a.Run(400);                                                        // a retarget: the RNG has moved
            a.S.Vx = 1.6;
            a.Until(() => a.W.State == WhiteState.Approach, 200);
            a.S.Vx = 0;
            a.Run(5);
            Assert.Equal(WhiteState.Approach, a.W.State);

            var b = new Rig(QuietLane(), "start") { X = 100 };         // any state: the snapshot overwrites it
            b.Run(30);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            b.X = a.X;
            bool grabbed = false;
            for (int k = 0; k < 900; k++)
            {
                a.Step(); b.Step();
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
                grabbed |= b.Emitted(WhiteEvent.Grab);
            }
            Assert.True(grabbed);
        }

        [Fact]
        public void TwoRuns_WithTheSameInputs_AreBitIdentical()
        {
            var traces = new List<string>[2];
            for (int run = 0; run < 2; run++)
            {
                var r = new Rig(WhiteParams.Chapter1());
                var trace = traces[run] = new List<string>();
                for (int i = 0; i < 3000; i++)
                {
                    r.X = 140 + 12 * (i / 3000.0);
                    r.S.Vx = (i / 200) % 2 == 0 ? 1.6 : 0.9;
                    if (i == 1500) { r.S.BeginStep(); Lane9Cues.RingBell(r.S.Noises); r.G.Step(Dt, Mech.Pose(r.X, r.Y)); }
                    else r.Step();
                    trace.Add(Mech.Dump(r.G) + string.Join(",", Mech.Events(r.G)));
                }
            }
            Assert.Equal(traces[0], traces[1]);
        }
    }
}
