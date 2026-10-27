using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Scenes.Dl07;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-07 as Core runs it in the prologue's chapter (<see cref="ChapterDefs.Prologue"/>), for what the golden trace does
    /// not play: the gallery gate at 0, 1 and 2 weights in the bucket (it walls him below 0.8; 0.38 per weight, 1.4 with
    /// two), the gallery collapse behind him (no way back), the respawns at <c>landing</c> and <c>gallery</c> (on the deck,
    /// in DL-07), the parcel slide back down, the letter on the rail, a weight lost down the chute and back by its home 4 s
    /// later, and DL-07 on its own (<see cref="Dl07Scene.Alone"/>). L1717, L1759, L1765, L2044, L3892–L3895, L4179–L4181,
    /// L4441–L4458, L4496–L4509, L4823–L4849, L4948–L4955, L4977–L5005, L7318, L7353–L7369, L8032–L8039.
    /// </summary>
    public class Dl07SceneSimTests
    {
        private const double Dt = 1.0 / 60;
        private static readonly MotorInput None = MotorInput.None;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Left = new MotorInput { Move = -1 };

        private static ChapterSim Begin(string cp)
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 280 };
            s.Begin(cp);
            return s;
        }

        private static Heap07 Rules(ChapterSim s) => (Heap07)s.RulesOf(s.Def.Scene(Dl07Scene.Id));
        private static CarrierLine Line(ChapterSim s) => s.Graph.Get<CarrierLine>("dl06.line");
        private static CarriedItem Weight(ChapterSim s, int i) => s.Graph.Get<CarriedItem>("dl07.weight" + i);

        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 6000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " y=" + s.Y + " act=" + SceneSim.KindOf(s) + " scene=" + s.Current?.Id);
        }

        /// <summary>Sets <paramref name="weights"/> in the carrier waiting at the dock (the loader as the motor's SetDownHigh f14 calls it, L4446).</summary>
        private static Carrier LoadDocked(ChapterSim s, params CarriedItem[] weights)
        {
            var line = Line(s);
            Until(s, None, x => line.DockLit);
            Carrier docked = null;
            for (int i = 0; i < line.Count; i++) if (line.At(i).State == CarrierState.Dock) docked = line.At(i);
            foreach (var w in weights)
            {
                Assert.True(line.Loader.Offer(new InteractionQuery(Dl06Scene_DockX, 0, 0, 1, true, false, HoldKind.Item, null, null), out _));
                line.Loader.OnPlaced(w);
                s.Step(None);
                Assert.Equal(ItemState.InCarrier, w.State);
            }
            return docked;
        }

        private const double Dl06Scene_DockX = 33 + 31.0;                                        // DOCK_X, L2457

        // ---- The gate: 0, 1 and 2 weights -----------------------------------------------------------------------------------
        /// <summary>Up for nothing: at <c>landing</c> the bucket is empty, the gate stays down and walls him 0.06 + HALF short of it (L4179).</summary>
        [Fact]
        public void Gate_NoWeights_StaysDown_AndWallsHimShortOfIt_L4179()
        {
            var s = Begin("landing");
            var r = Rules(s);
            Assert.Equal("DL-07", s.Current.Id);
            Assert.Equal(0, r.Bucket.Weights);
            for (int i = 0; i < 600; i++) s.Step(Right);
            Assert.Equal(0, r.Gate.Position);
            Assert.Equal(BucketGateState.Shut, r.Gate.State);
            Assert.Equal(Dl07Lane.GateX - Dl07Lane.GateGap, s.X, 9);
            Assert.Equal(1.6, s.Y, 12);
            Assert.Equal("landing", s.Checkpoints.Current.Name);
        }

        /// <summary>
        /// One weight sent up the ramp tips into the bucket at the landing: the gate rises 0.38 at 0.45 m/s and stalls with a
        /// strain (shake 0.15), still under 0.8: it walls him as before (L3892, L4826–L4831, L4179).
        /// </summary>
        [Fact]
        public void Gate_OneWeight_RisesTo0_38_StallsWithAStrain_AndStillWallsHim_L3892_L4831()
        {
            var s = Begin("landing");
            var r = Rules(s);
            var w = Weight(s, 0);
            LoadDocked(s, w);
            Until(s, None, x => w.State == ItemState.Tumble);
            Assert.True(r.Loading.TumbleOf(0) > 0);
            Until(s, None, x => r.Bucket.Weights == 1);
            Assert.Equal(ItemState.Gone, w.State);
            Assert.True(r.Loading.InBucket(0));
            bool strained = false;
            Until(s, None, x => { strained |= HasCue(x, ReturnToSender06.Shake, Heap07.StrainShake); return r.Gate.State == BucketGateState.Stalled; });
            Assert.True(strained);
            Assert.Equal(0.38, r.Gate.Position, 12);
            for (int i = 0; i < 600; i++) s.Step(Right);
            Assert.Equal(0.38, r.Gate.Position, 12);
            Assert.Equal(Dl07Lane.GateX - Dl07Lane.GateGap, s.X, 9);
            Assert.Equal("landing", s.Checkpoints.Current.Name);
        }

        /// <summary>
        /// Two weights in one tub (the second goes in beside the first), sent up: both tumble in, 0.18 s apart, the gate rises
        /// to 1.4 and opens, and he walks through it to <c>gallery</c> (L4449–L4450, L4992, L3892, L4948).
        /// </summary>
        [Fact]
        public void Gate_TwoWeights_OpensTo1_4_HeWalksThrough_ToGallery_L3892_L4948()
        {
            var s = Begin("landing");
            var r = Rules(s);
            var c = LoadDocked(s, Weight(s, 0), Weight(s, 1));
            Assert.Equal(1, c.Load1);
            Assert.Equal(2, c.Load2);
            Until(s, None, x => r.Bucket.Weights == 2);
            Assert.True(r.Loading.InBucket(0) && r.Loading.InBucket(1));
            Until(s, None, x => r.Gate.Engaged);
            Assert.Equal(1.4, r.Gate.Position, 12);
            Assert.False(r.Gate.Blocks);
            Until(s, Right, x => x.Checkpoints.Current.Name == "gallery");
            Assert.True(s.X > Dl07Scene.GalleryAt);
            Assert.Equal("DL-07", s.Current.Id);
        }

        /// <summary>The gate's target is 0.38 per weight, 1.4 with two (<c>gate6Target</c>, L3892), never down again.</summary>
        [Theory]
        [InlineData(0, 0.0)] [InlineData(1, 0.38)] [InlineData(2, 1.4)]
        public void Gate_Target_0_38PerWeight_1_4WithTwo_L3892(int weights, double target)
        {
            var s = Begin("landing");
            Assert.Equal(target, Rules(s).Gate.TargetFor(weights), 12);
        }

        // ---- The collapse ---------------------------------------------------------------------------------------------------
        /// <summary>
        /// Past <c>GALLERY6.trigger</c> on the gallery the panel behind him gives way; from then the lane walls him past it
        /// (<c>GALLERY6.x1 + 0.19</c>, L4181) while it swings and falls and once it is gone: there is no way back (L7355–L7362).
        /// </summary>
        [Fact]
        public void Collapse_GivesWayBehindHim_AndThereIsNoWayBack_L4181_L7355()
        {
            var s = Begin("gallery");
            var col = Rules(s).Collapse;
            Assert.Equal(CollapseState.Intact, col.State);
            Until(s, Right, x => col.State == CollapseState.Falling);
            Assert.True(s.X > Dl07Lane.CollapseTrigger);
            Assert.True(col.Engaged);
            double least = s.X;
            bool hit = false;
            for (int i = 0; i < 600; i++)
            {
                s.Step(Left);
                least = Math.Min(least, s.X);
                hit |= HasCue(s, ReturnToSender06.Shake, Heap07.CollapseShake);
            }
            Assert.Equal(CollapseState.Gone, col.State);
            Assert.True(hit);
            Assert.Equal(Dl07Lane.CollapseWall, least, 9);                                       // held at the torn edge, never back over the hole
            Assert.Equal(1.6, s.Y, 12);
            Assert.Equal("DL-07", s.Current.Id);
        }

        /// <summary>The collapse's timings: hit past 0.45 s, gone past 1.6 s; from <c>goods</c> on it is gone from the start (L7357–L7362, L4110).</summary>
        [Fact]
        public void Collapse_HitsAfter0_45s_GoneAfter1_6s_AndFromGoodsOnItIsGone()
        {
            var c = new Dl07Collapse("dl07.collapse") { OnGallery = () => true };
            var g = Mech.Graph("gallery", c);
            Mech.Run(g, 10, new PlayerPose(Dl07Lane.CollapseTrigger - 0.01, 1.6));
            Assert.Equal(CollapseState.Intact, c.State);
            int give = Mech.RunUntil(g, () => c.State == CollapseState.Falling, 5, new PlayerPose(Dl07Lane.CollapseTrigger + 0.01, 1.6));
            Assert.Equal(1, give);
            Assert.Equal(Dt, c.T, 12);
            int hit = Mech.RunUntil(g, () => Mech.Emitted(g, "dl07.collapse", CollapseEvent.Hit), 100);
            int ticks = 0;
            for (double t = 0; !(t > Dl07Collapse.SwingSeconds); ticks++) t += Dt;                 // collapseT += dt until > 0.45 (L7361)
            Assert.Equal(ticks, hit + 1);
            int gone = Mech.RunUntil(g, () => c.State == CollapseState.Gone, 200);
            Assert.InRange(c.T, 1.6, 1.6 + Dt);
            Assert.Equal(-62 * Math.PI / 180, c.SwingRad, 12);
            var off = new Dl07Collapse("dl07.collapse") { OnGallery = () => false };
            var g2 = Mech.Graph("gallery", off);
            Mech.Run(g2, 10, new PlayerPose(Dl07Lane.CollapseTrigger + 1, 0));                    // not on the gallery: nothing
            Assert.Equal(CollapseState.Intact, off.State);
            var later = new Dl07Collapse("dl07.collapse");
            Mech.Graph("goods", later);
            Assert.Equal(CollapseState.Gone, later.State);
            Assert.True(gone > 0);
        }

        // ---- Respawns -------------------------------------------------------------------------------------------------------
        /// <summary>
        /// Back down the slide, he boards a carrier on the floor and rides it up the ramp to the landing; there he hops off onto
        /// the gallery, staying on the carrier until the hop's last frame (the prototype's ride sync, L2959–L2964; Core's
        /// <see cref="Dl07LandingHopAct"/>), is up (<c>game.upper</c>) and brushes himself off (L2953–L2955). A respawn then puts
        /// him back at <c>landing</c>, in DL-07, on the deck (<c>c.upper</c>: <c>GALLERY.h</c>, L8039), the route to the exit,
        /// the belt running, the bucket empty and the gate down.
        /// </summary>
        [Fact]
        public void Respawn_AtLanding_AfterRidingBackUp_LandsInDl07_OnTheDeck_L2955_L8039()
        {
            var s = Begin("landing");
            var r = Rules(s);
            var line = Line(s);
            Until(s, Left, x => SceneSim.KindOf(x) == "dl07.slide");
            Until(s, None, x => SceneSim.KindOf(x) == null, 600);
            Weight(s, 1).MoveTo(ItemState.Gone, 0, 0);                                            // out of his way back to the junction
            Until(s, Left, x => x.X < 67.9);
            for (int i = 0; i < 30; i++) s.Step(None);
            Until(s, None, x => line.FindBoardable(x.X) != null && line.FindBoardable(x.X).State == CarrierState.Move);
            s.Step(new MotorInput { UsePressed = true });
            Until(s, None, x => x.Motor.Ride != null, 120);
            var c = line.Ride;
            bool hopped = false;
            Until(s, None, x =>
            {
                if (SceneSim.KindOf(x) == "Alight" && SceneSim.PhaseOf(x) == "Hop" && x.Motor.Ride != null)
                {
                    hopped = true;
                    Assert.Equal(c.Position, x.X, 12);                                             // on the carrier through the hop
                    Assert.Equal(c.RideY, x.Y, 12);
                }
                return r.Gallery.Upper;
            }, 3000);
            Assert.True(hopped);
            Assert.Equal(33 + 39.7, s.X, 9);                                                      // LANDING_X
            Assert.Equal(1.6, s.Y, 12);
            Assert.Equal(0, s.Z, 12);
            s.Step(None);
            Assert.Equal("quirk:BrushOff", SceneSim.KindOf(s) + ":" + SceneSim.PhaseOf(s));
            Assert.Equal("landing", s.Checkpoints.Current.Name);

            var changes = new System.Collections.Generic.List<(string, string, ExitDir)>();
            s.SceneChanged += (a, b, d) => changes.Add((a?.Id, b?.Id, d));
            s.Respawn();
            Assert.Empty(changes);                                                                 // DL-07 before and after
            Assert.Equal("DL-07", s.Current.Id);
            Assert.Equal(33 + 40.0, s.X, 12);
            Assert.Equal(1.6, s.Y, 12);
            Assert.Equal(3, s.Region);
            Assert.Equal(3, s.Lane.Region);
            Assert.True(r.Gallery.Upper);
            Assert.Equal(1.6, s.Lane.FloorAt(s.X), 12);
            Assert.Equal(0, r.Bucket.Weights);
            Assert.Equal(0, r.Gate.Position);
            Assert.True(line.Running);
            Assert.Equal(CarrierRoute.Exit, line.Route);
            for (int i = 0; i < 60; i++) s.Step(None);
            Assert.Equal(1.6, s.Y, 12);
            Assert.True(s.Grounded);
            Assert.Equal(ItemState.Floor, Weight(s, 1).State);                                    // the weights are back by the dock (L4098)
            Assert.Equal(Dl06Lane.Weight1X, Weight(s, 1).X, 12);
        }

        /// <summary>
        /// Through the open gate he reaches <c>gallery</c>; a respawn puts him back there, in DL-07, on the deck, with both weights
        /// in the bucket and the gate open (L4099, L4948). From a floor scene (DL-06 at <c>scanned</c>) the respawn crosses into DL-07.
        /// </summary>
        [Fact]
        public void Respawn_AtGallery_LandsInDl07_OnTheDeck_TheGateOpen_L4099_L4948()
        {
            var s = Begin("landing");
            var r = Rules(s);
            LoadDocked(s, Weight(s, 0), Weight(s, 1));
            Until(s, None, x => r.Gate.Engaged);
            Until(s, Right, x => x.Checkpoints.Current.Name == "gallery");
            for (int i = 0; i < 90; i++) s.Step(Right);
            s.Respawn();
            Assert.Equal("DL-07", s.Current.Id);
            Assert.Equal(33 + 42.3, s.X, 12);
            Assert.Equal(1.6, s.Y, 12);
            Assert.True(r.Gallery.Upper);
            Assert.Equal(2, r.Bucket.Weights);
            Assert.Equal(1.4, r.Gate.Position, 12);
            Assert.Equal(CollapseState.Intact, r.Collapse.State);
            for (int i = 0; i < 60; i++) s.Step(None);
            Assert.Equal(1.6, s.Y, 12);
            Assert.True(s.Grounded);

            var f = Begin("scanned");
            Assert.Equal("DL-06", f.Current.Id);
            Assert.True(f.Checkpoints.Reach("gallery"));                                           // derived from the checkpoint: the snapshot is the floor's
            var changes = new System.Collections.Generic.List<(string, string, ExitDir)>();
            f.SceneChanged += (a, b, d) => changes.Add((a?.Id, b?.Id, d));
            f.Begin("gallery");
            Assert.Equal(new[] { ("DL-06", "DL-07", ExitDir.None) }, changes);
            Assert.Equal(1.6, f.Y, 12);
            Assert.Equal(1.4, Rules(f).Gate.Position, 12);
        }

        // ---- The slide, the letter, the doorway -----------------------------------------------------------------------------
        /// <summary>
        /// Walking left off the gallery's left end he sits into the slide and is carried down it to the sorting floor in about
        /// 2 s, facing −x; there he is down (<c>game.upper = false</c>), 0.1 short of its foot (L4952–L4955, L4496–L4508).
        /// </summary>
        [Fact]
        public void Slide_OffTheGallerysLeftEnd_DownToTheFloor_L4496_L4508_L4952()
        {
            var s = Begin("landing");
            var r = Rules(s);
            Until(s, Left, x => SceneSim.KindOf(x) == "dl07.slide");
            Assert.Equal("act", SceneSim.PhaseOf(s));
            Assert.True(s.X >= Dl07Lane.Left - 1e-9 && s.X < Dl07Scene.SlideFrom, s.X.ToString("R"));
            int n = Until(s, None, x => SceneSim.KindOf(x) == null, 600);
            Assert.InRange(n * Dt, 1.5, 3.0);
            Assert.False(r.Gallery.Upper);
            Assert.Equal(33 + 35.70 - 0.1, s.X, 12);
            Assert.Equal(0, s.Y, 12);
            Assert.Equal(0, s.Z, 12);
            Assert.True(s.Grounded);
            Assert.Equal(-1, s.Motor.Facing);
            Assert.Equal(0, s.Lane.FloorAt(s.X), 12);
            Assert.Equal(Dl06Lane.WeightH, s.Lane.SurfaceAt(Dl06Lane.Weight1X), 12);           // the floor's weights are solid down here again
            Assert.Equal("DL-07", s.Current.Id);                                                 // past landing: still the heap
        }

        /// <summary>Up on the gallery the floor's weights are not under him (L4154) and the walls are the gallery's (L1759, L1765, L4180).</summary>
        [Fact]
        public void GalleryLane_TheDeck_ItsWalls_AndNotTheFloorsWeights_L1717_L4154()
        {
            var s = Begin("landing");
            Assert.Equal(1.6, s.Lane.FloorAt(70), 12);
            Assert.Equal(1.6, s.Lane.SurfaceAt(Dl06Lane.Weight1X), 12);
            s.Lane.Limits(73, 1.6, out double lo, out double hi);
            Assert.Equal(Dl07Lane.Left, lo, 12);
            Assert.Equal(Dl07Lane.GateX - Dl07Lane.GateGap, hi, 12);
            s.Lane.Limits(76, 1.6, out lo, out hi);
            Assert.Equal(Dl07Lane.Right, hi, 12);
            var f = Begin("scanned");
            Assert.Equal(Dl06Lane.WeightH, f.Lane.SurfaceAt(Dl06Lane.Weight1X), 12);
            f.Lane.Limits(65, 0, out lo, out hi);
            Assert.Equal(Dl06Lane.Right, hi, 12);
        }

        /// <summary>The letter on the rail falls to the deck when he passes under it on the gallery, in 0.6 s, once (L4840–L4846).</summary>
        [Fact]
        public void Letter_FallsWhenHePassesUnderIt_OnTheGallery_L4840()
        {
            var s = Begin("gallery");
            var l = Rules(s).Letter;
            Assert.Equal(HeapLetterState.Rail, l.State);
            Assert.Equal(-1, l.T);
            Until(s, Right, x => l.State == HeapLetterState.Falling);
            Assert.True(Math.Abs(s.X - Dl07HeapLetter.X) < Dl07HeapLetter.Reach);
            int n = Until(s, None, x => l.State == HeapLetterState.Floor, 100);
            Assert.Equal(35, n);                                                                  // 36 ticks of 1/60 from the step it let go
            Assert.Equal(1, l.Fall);
            var off = new Dl07HeapLetter("dl07.heapLetter");                                    // OnGallery: never by default (not from the floor)
            var g = Mech.Graph("gallery", off);
            Mech.Run(g, 10, new PlayerPose(Dl07HeapLetter.X, 0));
            Assert.Equal(HeapLetterState.Rail, off.State);
        }

        /// <summary>Past <c>REGION4_X</c> on the gallery he is in region 4, at <c>goods</c>, in DL-08, on its deck (L2044).</summary>
        [Fact]
        public void Doorway_PastRegion4X_Region4_Goods_DL08_L2044()
        {
            var s = Begin("gallery");
            Until(s, Right, x => x.Region == 4);
            Assert.Equal("goods", s.Checkpoints.Current.Name);
            Assert.True(s.X > Dl07Scene.DoorwayX);
            Assert.Equal("DL-08", s.Current.Id);
            Assert.Equal(4, s.Lane.Region);
            Assert.Equal(Dl07Lane.Deck, s.Y);
            Assert.False(s.Exited);
        }

        // ---- Weights down the chute, refused --------------------------------------------------------------------------------
        /// <summary>A weight sent to the chute is lost with the post, and stands by its home again 4 s later (L2734, L5004).</summary>
        [Fact]
        public void Weight_DownTheChute_IsLost_AndBackByItsHome4sLater_L5004()
        {
            var s = Begin("scanned");
            var r = Rules(s);
            var w = Weight(s, 1);
            LoadDocked(s, w);
            Until(s, None, x => w.State == ItemState.Gone);
            Assert.False(r.Loading.InBucket(1));
            Assert.Equal(4, r.Loading.ReturnsIn(1), 12);                                        // from the next step on
            int n = Until(s, None, x => w.State == ItemState.Floor, 400);
            Assert.Equal(240, n);
            Assert.Equal(Dl06Lane.Weight1X, w.X, 12);
            Assert.Equal(0, w.BaseY);
            Assert.Equal(0, r.Bucket.Weights);
        }

        /// <summary>Set down after the carrier has gone, the weight lies on the floor at his feet (L4453).</summary>
        [Fact]
        public void Weight_TheCarrierGoneBeforeTheRelease_LiesAtHisFeet_L4453()
        {
            var s = Begin("scanned");
            var line = Line(s);
            var w = Weight(s, 0);
            Until(s, None, x => line.DockLit);
            Assert.True(line.Loader.Offer(new InteractionQuery(Dl06Scene_DockX, 0, 0, 1, true, false, HoldKind.Item, null, null), out _));
            var c = line.At(0);
            Until(s, None, x => c.State == CarrierState.Tip);                                    // gone to the chute's end
            line.Loader.OnPlaced(w);
            s.Step(None);
            Assert.Equal(ItemState.Floor, w.State);
            Assert.Equal(s.X, w.X, 12);
            Assert.Equal(0, w.BaseY);
        }

        // ---- The bucket fed from the line's log ------------------------------------------------------------------------------
        /// <summary>
        /// Fed from the line's log, a weight starts its tumble on the step the carrier lets it go and lands 42 ticks later, as
        /// <c>placeItem</c> moves it in the same step's <c>updateCh1</c> (L4957–L4962); the second of a tub 0.18 s on.
        /// </summary>
        [Fact]
        public void Bucket_FedFromTheLinesLog_TumblesFromTheTipsStep_Lands42TicksLater_L4957()
        {
            var feed = new Feeder("t.line");
            var bucket = new GateBucket("dl07.bucket", new GateBucketParams { Feed = "t.line" });
            var g = Mech.Graph("landing", feed, bucket);
            feed.Next = 1;
            Mech.Run(g, 1);
            Assert.Equal(1, bucket.Tumbling);
            Assert.Equal(Dt, bucket.TumbleSeconds(0), 12);
            int land = Mech.RunUntil(g, () => bucket.Weights == 1, 100);
            Assert.Equal(41, land);                                                              // 42 ticks in all
            Assert.Throws<InvalidOperationException>(() => Mech.Graph("landing", new GateBucket("t.bucket", new GateBucketParams { Feed = "t.line" }), new Feeder("t.line")));   // the line steps first
        }

        // ---- DL-07 on its own, and allocation -----------------------------------------------------------------------------
        /// <summary>DL-07 simulated on its own builds the whole floor and the gallery (the floor's mechanisms once, the loader registered).</summary>
        [Fact]
        public void Alone_BuildsTheFloorAndTheGallery()
        {
            var s = new SceneSim(Dl07Scene.Alone()) { Clock = 280 };
            s.Begin("landing");
            Assert.NotNull(s.Graph.Get<CarrierLine>("dl06.line"));
            Assert.NotNull(s.Graph.Get<BucketGate>("dl07.gate"));
            Assert.True(((Heap07)s.Rules).Gallery.Upper);
            Assert.Equal(1.6, s.Lane.FloorAt(73), 12);
            var chapter = new ChapterSim(ChapterDefs.Prologue());
            Assert.Equal(chapter.Graph.Count, s.Graph.Count + CountOutsideRegion3(chapter));
        }

        private static int CountOutsideRegion3(ChapterSim c)
        {
            int n = 0;
            foreach (var scene in c.Def.Scenes) if (scene.Region != 3) n += c.MechanismsOf(scene).Count;
            return n;
        }

        /// <summary>A step on the gallery allocates nothing: the walk to the doorway past the letter and the collapse, carriers running.</summary>
        [Fact]
        public void Step_OnTheGallery_AllocatesNothing()
        {
            var s = Begin("gallery");
            for (int i = 0; i < 20; i++) s.Step(None);                                          // warm up
            var walk = new MotorInput { Move = 1, RunModifierHeld = true };
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 200; i++) s.Step(walk);
            Assert.Equal(0, GC.GetAllocatedBytesForCurrentThread() - before);
        }

        private static bool HasCue(ChapterSim s, Cues.CueId id, int arg)
        {
            foreach (var c in s.Cues) if (c.Id == id && c.Arg == arg) return true;
            return false;
        }

        /// <summary>Emits the line's LoadToBucket for <see cref="Next"/> on its next step.</summary>
        private sealed class Feeder : Mechanism
        {
            public int Next;
            public Feeder(MechanismId id) : base(id) { }
            public override void Reset(in Checkpoint cp) { }
            public override void Step(in StepContext ctx)
            {
                if (Next != 0) { Emit(ctx, (int)CarrierLineEvent.LoadToBucket, Next); Next = 0; }
            }
            protected override void WriteFields(ISnapshotWriter w) { }
            protected override void ReadFields(ISnapshotReader r) { }
        }
    }
}
