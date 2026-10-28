using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Presentation;
using DeadLetter.Core.Scenes;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-23 (#34): the light pool (§4.20, L8536–L8598) and its region lists (L2622–L2657), the mix's snapshots and the
    /// moment duck, the AudioWorld's emitters and conditions (L1145–L1211, L6577–L6598), and the DL-06 carriers' pooled views.
    /// </summary>
    public class PresentationTests
    {
        /// <summary>The relay lamp casts a shadow only off touch devices (<c>castShadow = !touch</c>, L1466): not on Switch handheld.</summary>
        [Fact]
        public void RelayShadow_OnlyOffTouchDevices_L1466()
        {
            LightDef Relay(bool touch) => PrologueLights.Build(touch).Single(d => d.Name == "relay");
            Assert.True(Relay(false).Shadow);
            Assert.False(Relay(true).Shadow);
            Assert.True(LightPoolBudget.SwitchHandheld.Touch);
            Assert.False(LightPoolBudget.SwitchDocked.Touch);
            Assert.False(LightPoolBudget.Prototype.Touch);
        }

        // ---- Light regions and zones ---------------------------------------------------------------------------------------

        private static string[] VisibleNames(int r, LightZone zone)
            => PrologueLights.Build().Where(d => LightRegions.Visible(d.Group, r, zone, false)).Select(d => d.Name).ToArray();

        [Fact]
        public void Region1_ShowsTheDepotsLights()
        {
            Assert.Equal(new[] { "hemi", "rim", "relay", "work", "kick", "search", "cord", "cable", "door", "crank", "back", "pool", "cot" },
                VisibleNames(1, LightZone.None));
        }

        [Fact]
        public void Region2_ShowsTheHallsAndRacks_TheRationHallSwapsDl01sAndTheSortingHallsOut()
        {
            var halls = VisibleNames(2, LightZone.None);
            foreach (var n in new[] { "search", "cable", "door", "back", "plateLamp", "rack0", "scanner", "sh0", "sh6", "bay", "voice0" }) Assert.Contains(n, halls);
            foreach (var n in new[] { "relay", "work", "crank", "rationStrip", "floor0", "pitSky" }) Assert.DoesNotContain(n, halls);
            var ration = VisibleNames(2, LightZone.Ration);
            foreach (var n in new[] { "rationStrip", "rationFill", "candles", "plateLamp", "bay", "scanner" }) Assert.Contains(n, ration);
            foreach (var n in new[] { "search", "cable", "door", "back", "sh0", "voice0" }) Assert.DoesNotContain(n, ration);   // r ≤ 2 && !ration
        }

        [Fact]
        public void Region3_ShowsTheSortingFloor_AndTheScannerStays()
        {
            var floor = VisibleNames(3, LightZone.None);
            foreach (var n in new[] { "floor0", "pit2", "gallery1", "pitSky", "scanner", "secret0", "spill0", "voice1", "hemi", "kick" }) Assert.Contains(n, floor);
            foreach (var n in new[] { "plateLamp", "rack0", "bay", "search", "sh0", "rationStrip" }) Assert.DoesNotContain(n, floor);
        }

        [Fact]
        public void TheZones_HaveTheirHysteresis()
        {
            Assert.Equal(LightZone.None, LightRegions.ZoneFor(2, 2, 47.3, LightZone.None));
            Assert.Equal(LightZone.Ration, LightRegions.ZoneFor(2, 2, 47.5, LightZone.None));        // RATION5.x0 − 0.5
            Assert.Equal(LightZone.Ration, LightRegions.ZoneFor(2, 2, 47.0, LightZone.Ration));      // − 1.0 once inside
            Assert.Equal(LightZone.None, LightRegions.ZoneFor(2, 2, 46.8, LightZone.Ration));
            Assert.Equal(LightZone.UpOnly, LightRegions.ZoneFor(4, 4, 117.9, LightZone.None));      // UPONLY.x0 − 1.0
            Assert.Equal(LightZone.None, LightRegions.ZoneFor(4, 3, 120, LightZone.None));          // game.region ≥ 4
            Assert.Equal(LightZone.None, LightRegions.ZoneFor(3, 3, 60, LightZone.None));
        }

        [Fact]
        public void TheLightRegion_LagsTheGameRegion_WhereThePrototypeSwitchesEarlyOrLate()
        {
            var t = new LightRegionTracker();
            t.Place(1, false, 3);
            Assert.Equal(1, t.Region);
            t.Update(1, 10.4, 10.4, transitLeg: 0, scanning: false);
            Assert.Equal(1, t.Region);
            t.Update(1, 10.4, 10.4, transitLeg: 1, scanning: false);                                // the passage's first leg (L2149)
            Assert.Equal(2, t.Region);
            Assert.True(t.Changed);
            t.Update(3, 61, 61, -1, scanning: false);                                                // DL-06's floor before the scan
            Assert.Equal(2, t.Region);
            Assert.Equal(LightZone.Ration, t.Zone);                                                  // as the prototype's (x > 47.4, light region 2)
            t.Update(3, 61.9, 61.9, -1, scanning: true);                                             // the scan starts (L2781)
            Assert.Equal(3, t.Region);
            Assert.Equal(LightZone.None, t.Zone);
            t.Place(3, scanned: false, 61);                                                          // resetWorld (L8055)
            Assert.Equal(2, t.Region);
            t.Place(3, scanned: true, 66);
            Assert.Equal(3, t.Region);
        }

        // ---- The pool ------------------------------------------------------------------------------------------------------

        private static LightDef P(string name, double x, double intensity, double distance = 3, bool kick = false)
            => new LightDef { Name = name, Kind = LightKind.Point, Group = LightGroup.Always, Intensity = intensity, Distance = distance, Position = new Vec3(x, 1, 0), Kick = kick };

        private static LightDef S(string name, double x, bool shadow, double intensity = 5)
            => new LightDef { Name = name, Kind = LightKind.Spot, Group = LightGroup.Always, Intensity = intensity, Distance = 5, Position = new Vec3(x, 2, 0), Shadow = shadow };

        [Fact]
        public void ThePool_TakesTheBestScoringLitProxies_UpToItsBudget()
        {
            var defs = Enumerable.Range(0, 14).Select(i => P("p" + i, i, 1)).ToArray();
            var pool = new LightPool(defs);
            pool.Assign(cameraX: 0);
            Assert.Equal(10, Enumerable.Range(0, pool.PointSlots).Count(s => pool.Point(s) >= 0));
            Assert.Equal(Enumerable.Range(0, 10).ToArray(), Enumerable.Range(0, 10).Select(pool.Point).ToArray());   // nearest first
            pool.SetVisible(0, false);
            pool.SetLevel(1, 0);
            pool.Assign(0);
            Assert.DoesNotContain(0, Enumerable.Range(0, 10).Select(pool.Point));                    // lightOn: hidden or dark
            Assert.DoesNotContain(1, Enumerable.Range(0, 10).Select(pool.Point));
            Assert.Equal(11, pool.Wanted);                                                           // p13: 10 m beyond its 3 m reach
        }

        [Fact]
        public void TheScore_IsThePrototypes_AndFarProxiesAreSkipped()
        {
            var pool = new LightPool(new[] { P("near", 2, 2, 4), P("far", 30, 100, 4), P("kick", 50, 0.1, kick: true) });
            Assert.Equal(2 * 4 / (1 + 0 + 0.05 * 4), pool.Score(0, 0), 12);                         // intensity·distance / (1 + gap² + 0.05·dx²)
            double gap = 30 - 4;
            Assert.True(double.IsNaN(pool.Score(1, 0)) == (gap > 9));                                // > 9 m beyond its reach
            Assert.True(pool.Score(2, 45) > LightPool.KickScore);
            pool.Assign(45);
            Assert.Equal(2, pool.Point(0));                                                          // the kick first
        }

        [Fact]
        public void ShadowedSpots_BeyondTheShadowSlots_LightAsPlainSpots()
        {
            var defs = new[] { S("a", 0, true, 9), S("b", 0.5, true, 8), S("c", 1, true, 7), S("d", 0, false, 1) };
            var pool = new LightPool(defs);
            pool.Assign(0);
            Assert.Equal(new[] { 0, 1 }, new[] { pool.SpotShadow(0), pool.SpotShadow(1) });
            Assert.Equal(new[] { 2, 3, -1, -1 }, Enumerable.Range(0, 4).Select(pool.Spot).ToArray());
        }

        [Fact]
        public void EqualScores_KeepTheProxiesOrder()
        {
            var defs = new[] { P("a", 1, 1), P("b", -1, 1), P("c", 1, 1) };
            var pool = new LightPool(defs, new LightPoolBudget { Point = 2 });
            pool.Assign(0);
            Assert.Equal(new[] { 0, 1 }, new[] { pool.Point(0), pool.Point(1) });
        }

        [Fact]
        public void Hemispheres_BecomeTheAmbient()
        {
            var hemi = PrologueLights.Build()[0];
            var pool = new LightPool(new[] { hemi });
            pool.Assign(0);
            Assert.Equal(0, pool.Hemisphere(0));
            Assert.Equal(Rgb.Hex(0x26332f).G * 0.45, pool.AmbientSky.G, 12);
            Assert.Equal(Rgb.Hex(0x0b0b0a).R * 0.45, pool.AmbientGround.R, 12);
            Assert.Equal((pool.AmbientSky.B + pool.AmbientGround.B) / 2, pool.AmbientEquator.B, 12);
        }

        [Fact]
        public void TheBudgets_AreTheTiers()
        {
            var pc = LightPoolBudget.For(Platform.PlatformKind.Desktop);
            Assert.Equal((10, 4, 2, 2, 2), (pc.Point, pc.Spot, pc.SpotShadow, pc.Directional, pc.Hemisphere));   // LIGHT_POOL, L8542
            var hand = LightPoolBudget.For(Platform.PlatformKind.Switch, docked: false);
            Assert.Equal((6, 3, 1, 1), (hand.Point, hand.Spot, hand.SpotShadow, hand.Directional));            // §8.2
            var pool = new LightPool(PrologueLights.Build(), hand);
            Assert.Equal(6, pool.PointSlots);
        }

        /// <summary>The pool in each of the prologue's places: only lit proxies of the place's lists, within the budget.</summary>
        [Theory]
        [InlineData("start", 1, LightZone.None, "relay")]
        [InlineData("hall", 1, LightZone.None, "work")]
        [InlineData("room", 2, LightZone.None, "sh2")]
        [InlineData("solved", 2, LightZone.None, "plateLamp")]
        [InlineData("bay", 2, LightZone.None, "bay")]
        [InlineData("ration", 2, LightZone.Ration, "rationStrip")]
        [InlineData("scanned", 3, LightZone.None, "pitSky")]
        public void ThePool_PerPlace(string checkpoint, int lightRegion, LightZone zone, string expect)
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 100 };
            var view = new ChapterPresentation(sim);
            sim.Begin(checkpoint);
            view.OnPlaced();
            sim.Step(default);
            view.AfterStep(false, false);
            for (int i = 0; i < 30; i++) view.Frame(sim.Clock, 1 / 60.0, sim.X, calm: false);
            var pool = view.Lighting.Pool;
            Assert.Equal(lightRegion, view.Lighting.Regions.Region);
            Assert.Equal(zone, view.Lighting.Regions.Zone);
            var assigned = new List<int>();
            for (int s = 0; s < pool.PointSlots; s++) if (pool.Point(s) >= 0) assigned.Add(pool.Point(s));
            for (int s = 0; s < pool.SpotSlots; s++) if (pool.Spot(s) >= 0) assigned.Add(pool.Spot(s));
            for (int s = 0; s < pool.SpotShadowSlots; s++) if (pool.SpotShadow(s) >= 0) assigned.Add(pool.SpotShadow(s));
            for (int s = 0; s < pool.DirectionalSlots; s++) if (pool.Directional(s) >= 0) assigned.Add(pool.Directional(s));
            Assert.All(assigned, i => Assert.True(pool.On(i) && LightRegions.Visible(pool[i].Group, lightRegion, zone, false), pool[i].Name));
            Assert.Equal(assigned.Count, assigned.Distinct().Count());
            Assert.Contains(expect, assigned.Select(i => pool[i].Name));
            Assert.Equal("kick", pool[pool.Point(0)].Name);
            Assert.Equal("rim", pool[pool.Directional(0)].Name);
            Assert.Equal("hemi", pool[pool.Hemisphere(0)].Name);
            Assert.True(pool.AmbientSky.G > 0);
        }

        [Fact]
        public void Playthrough_LightsEveryPlace_AndNeverAssignsADarkProxy()
        {
            var p = ChapterSoundsTests.Run();
            foreach (var place in new[] { (1, LightZone.None), (2, LightZone.None), (2, LightZone.Ration), (3, LightZone.None) }) Assert.Contains(place, p.LightPlaces);
            Assert.Equal(0, p.AssignedInvisible);
            Assert.Equal(0, p.LightsOverBudget);
        }

        [Fact]
        public void CalmMode_SteadiesTheFlickers()
        {
            var calm = Enumerable.Range(0, 2000).Select(i => PrologueLighting.RationFlicker(i * 0.05, calm: true)).Distinct().ToArray();
            Assert.Equal(new[] { 1.0 }, calm);                                                      // L4928
            var live = Enumerable.Range(0, 2000).Select(i => PrologueLighting.RationFlicker(i * 0.05, calm: false)).ToArray();
            Assert.Contains(live, v => v <= 0.25 + 1e-9);                                            // the strip's stutter
            Assert.True(RackRows.Row(0, 1.0 + 0.3, calm: true) > 0 && RackRows.Row(0, 1.0 + 0.3, calm: true) < 1);   // eased, not flickered (L2418)
            // The live cable: a flicker while it arcs, a steady 0.4 in calm mode (L7941).
            foreach (bool c in new[] { false, true })
            {
                var sim = new ChapterSim(ChapterDefs.Prologue());
                var view = new ChapterPresentation(sim);
                sim.Begin("start");
                view.OnPlaced();
                int cable = Array.FindIndex(Enumerable.Range(0, view.Lighting.Pool.Count).Select(i => view.Lighting.Pool[i]).ToArray(), d => d.Name == "cable");
                var levels = new HashSet<double>();
                for (int i = 0; i < 60 * 12; i++)
                {
                    sim.Step(default);
                    view.AfterStep(false, c);
                    view.Frame(sim.Clock, 1 / 60.0, sim.X, c);
                    if (view.Lighting.Pool.Level(cable) > 0) levels.Add(view.Lighting.Pool.Level(cable));
                }
                Assert.NotEmpty(levels);
                if (c) Assert.Equal(new[] { 0.4 }, levels.ToArray());
                else Assert.Superset(new HashSet<double> { 2.5, 0.75 }, levels);
            }
        }

        // ---- The mix -------------------------------------------------------------------------------------------------------

        [Fact]
        public void EachPlace_HasItsSnapshot()
        {
            Assert.Equal(MixSnapshot.Depot, MixRules.SnapshotFor(1, LightZone.None));
            Assert.Equal(MixSnapshot.Halls, MixRules.SnapshotFor(2, LightZone.None));
            Assert.Equal(MixSnapshot.RationHall, MixRules.SnapshotFor(2, LightZone.Ration));
            Assert.Equal(MixSnapshot.SortingFloor, MixRules.SnapshotFor(3, LightZone.Ration));
            Assert.Equal(MixSnapshot.UpOnly, MixRules.SnapshotFor(4, LightZone.UpOnly));
            Assert.Equal("RationHall", MixRules.Name(MixSnapshot.RationHall));
            var p = ChapterSoundsTests.Run();
            Assert.Superset(new HashSet<MixSnapshot> { MixSnapshot.Depot, MixSnapshot.Halls, MixSnapshot.RationHall, MixSnapshot.SortingFloor }, p.Snapshots);
            Assert.Subset(new HashSet<MixSnapshot> { MixSnapshot.Depot, MixSnapshot.Halls, MixSnapshot.RationHall, MixSnapshot.SortingFloor }, p.Snapshots);
        }

        [Fact]
        public void APlacementSnaps_ACrossingBlends()
        {
            var m = new MixState();
            m.Place(1, LightZone.None);
            m.Update(1, LightZone.None, false, 1 / 60.0);
            Assert.True(m.SnapshotChanged);
            Assert.Equal(0, m.TransitionSeconds);
            m.Update(1, LightZone.None, false, 1 / 60.0);
            Assert.False(m.SnapshotChanged);
            m.Update(2, LightZone.None, false, 1 / 60.0);
            Assert.True(m.SnapshotChanged);
            Assert.Equal(MixSnapshot.Halls, m.Snapshot);
            Assert.Equal(MixRules.SnapshotTransition, m.TransitionSeconds);
        }

        [Fact]
        public void ADirectedMoment_DucksTheSfxAndTheEmitters_AndLetsGo()
        {
            var m = new MixState();
            m.Place(2, LightZone.None);
            for (int i = 0; i < 60 * 4; i++) m.Update(2, LightZone.None, true, 1 / 60.0);
            Assert.Equal(MixRules.MomentSfxDb, m.OffsetDb(AudioGroup.Sfx), 2);
            Assert.Equal(MixRules.MomentAmbienceDb, m.OffsetDb(AudioGroup.Ambience), 2);
            Assert.Equal(0, m.OffsetDb(AudioGroup.Music), 9);
            Assert.Equal(0, m.OffsetDb(AudioGroup.Master), 9);
            Assert.Equal(-6 + -10.0, m.Decibels(-10, AudioGroup.Sfx), 2);                          // added to the options' level
            Assert.Equal(AudioLevels.SilentDb, m.Decibels(-79, AudioGroup.Sfx));
            for (int i = 0; i < 60 * 10; i++) m.Update(2, LightZone.None, false, 1 / 60.0);
            Assert.InRange(m.OffsetDb(AudioGroup.Sfx), -0.05, 0);
            // DL-04's kin moment ducks it in the bot's run.
            var p = ChapterSoundsTests.Run();
            Assert.True(p.DeepestSfxDuckDb < -5, "the kin moment never ducked: " + p.DeepestSfxDuckDb);
            Assert.True(p.DeepestAmbienceDuckDb < -8);
        }

        // ---- The AudioWorld ------------------------------------------------------------------------------------------------

        [Fact]
        public void TheConditions_AreTheSims()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var w = new AmbienceWorld(sim);
            sim.Begin("start");
            Assert.False(w.Condition(AmbienceWorld.Released));
            Assert.False(w.Condition(PrologueEmitters.Revealed));
            Assert.True(w.Condition(null));
            Assert.False(w.Condition(PrologueEmitters.LessonRunning));
            sim.Begin("shutter");
            Assert.True(w.Condition(AmbienceWorld.Released));
            sim.Begin("solved");
            Assert.True(w.Condition(PrologueEmitters.Revealed));
            Assert.Equal(AmbienceWorld.Released, VoiceCatalog.Placements.First(v => v.Id == "tan_depot_1").Condition);   // the tannoy's
        }

        [Fact]
        public void EveryPrologueEmitter_SoundsInTheBotsRun_AndNoLaterOne()
        {
            var p = ChapterSoundsTests.Run();
            for (int i = 0; i < PrologueEmitters.All.Length; i++)
            {
                var e = PrologueEmitters.All[i];
                if (e.Region <= 3 && i != 7) Assert.True(p.EmitterPeak[i] > 0.05, "emitter " + i + " (" + e.Note + ") never sounded");
                if (e.Region > 3) Assert.Equal(0, p.EmitterPeak[i]);
                if (e.Region <= 3 && e.IsEvent && i != 7) Assert.True(p.EmitterBlips[i] > 0, "emitter " + i + " never blipped");
            }
        }

        [Fact]
        public void TheDispatchBoardsTick_BlipsEvery0_9s_InReach()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var w = new AmbienceWorld(sim);
            sim.Begin("start");
            sim.Motor.Place(1.2, 0, 1);
            var blips = new List<double>();
            for (int i = 0; i < 60 * 5; i++)
            {
                double now = i / 60.0;
                w.Update(now, 1 / 60.0);
                if (w.Blip(0)) blips.Add(now);
            }
            Assert.True(blips.Count >= 5);
            Assert.All(blips.Zip(blips.Skip(1), (a, b) => b - a), g => Assert.InRange(g, 0.9 - 1e-9, 0.9 + 1 / 30.0));
            Assert.Equal(0.45 * Math.Pow(1 - 0.2 / 3, 2), w.Gain(0), 2);                             // level·k² (L1203–L1208)
            Assert.Equal(0, w.Gain(2));                                                             // DL-02's fan: another region
        }

        [Fact]
        public void TheBed_IsTheRegionsAmbience()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var w = new AmbienceWorld(sim);
            sim.Begin("start");
            Assert.Equal("lower_works", w.Bed.Name);
            sim.Begin("ration");
            Assert.Equal("order", w.Bed.Name);                                                     // the Ration Hall (L8150)
            sim.Begin("scanned");
            Assert.Equal("lower_works", w.Bed.Name);                                               // the floor after the scan (L8151)
        }

        // ---- Carriers ------------------------------------------------------------------------------------------------------

        [Fact]
        public void EachCarrier_KeepsItsView_FromSpawnToRemoval()
        {
            var p = ChapterSoundsTests.Run(201, false);                                              // a player who lets the line run
            Assert.True(p.MostCarriers >= 2, "carriers seen at once: " + p.MostCarriers);
            Assert.Equal(0, p.CarrierSlotJumps);
            Assert.Equal(0, p.CarrierOverflow);
        }

        [Fact]
        public void CarrierViews_FollowTheLine_AndInterpolate()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 200 };
            var view = new ChapterPresentation(sim);
            sim.Begin("scanned");
            view.OnPlaced();
            var c = view.Carriers;
            var line = c.Line;
            int maxLive = 0;
            for (int i = 0; i < 60 * 40; i++)
            {
                sim.Step(default);
                view.AfterStep(false, false);
                int live = Enumerable.Range(0, c.Capacity).Count(c.Active);
                Assert.Equal(line.Count, live);
                maxLive = Math.Max(maxLive, live);
                for (int s = 0; s < c.Capacity; s++)
                {
                    if (!c.Active(s)) continue;
                    var carrier = Enumerable.Range(0, line.Count).Select(line.At).Single(k => k.Seq == c.SeqOf(s));
                    Assert.Equal(carrier.Position, c.Pose(s, 1).X, 12);
                    Assert.Equal(carrier.Y, c.Pose(s, 1).Y, 12);
                    Assert.Equal(carrier.TipRad, c.Pose(s, 1).Tip, 12);
                    var mid = c.Pose(s, 0.5);
                    Assert.InRange(mid.X, Math.Min(c.Pose(s, 0).X, carrier.Position) - 1e-12, Math.Max(c.Pose(s, 0).X, carrier.Position) + 1e-12);
                }
            }
            Assert.True(maxLive >= 2, "the line never ran: " + maxLive);
        }
    }
}
