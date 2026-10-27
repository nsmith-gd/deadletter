using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Routes;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Routes, carriers and belts (§4.13h): the DL-06/07 return line and its levers, DL-08's returns belt.</summary>
    public class RouteTests
    {
        // S along the routes (L2471–L2477): dock 1.25, junction 4.85, chute end 6.75, return lift 6.15, landing, exit end.
        private static readonly double SLanding = 4.85 + Math.Sqrt(0.65 * 0.65 + 0.32 * 0.32) + Math.Sqrt(3.25 * 3.25 + 1.28 * 1.28) + 1.2;

        private sealed class LineRig
        {
            public readonly TestSource Belt, Points;
            public readonly CarrierLine Line;
            public readonly MechanismGraph G;

            public LineRig(string cp = "scanned", bool running = true, bool exit = false)
            {
                Belt = new TestSource("dl06.stopLever") { Engaged = running };
                Points = new TestSource("dl06.points") { Engaged = exit };
                Line = new CarrierLine("dl06.line", CarrierLineParams.Dl06Line());
                G = Mech.Graph(cp, Belt, Points, Line);
            }

            public Carrier First => Line.Count > 0 ? Line.At(0) : null;

            public int Until(Func<bool> f, int max = 6000, PlayerPose? pose = null) => Mech.RunUntil(G, f, max, pose);

            public bool Emitted(CarrierLineEvent e) => Mech.Emitted(G, "dl06.line", e);

            public List<MechanismEvent> All(CarrierLineEvent e)
            {
                var list = new List<MechanismEvent>();
                foreach (var ev in Mech.Events(G)) if (ev.Id == "dl06.line" && ev.Kind == MechanismEventKind.Event && ev.Code == (int)e) list.Add(ev);
                return list;
            }
        }

        // ---- The line: spawn, rise, dock, belt ------------------------------------------------------------------------

        [Fact]
        public void Line_Geometry_MatchesThePrototypesLengths_L2475_L2477()
        {
            var r = new LineRig();
            Assert.Equal(1.25, r.Line.SDock, 12);
            Assert.Equal(4.85, r.Line.SJunction, 12);
            Assert.Equal(SLanding, r.Line.SLanding, 12);
            Assert.Equal(6.75, r.Line.SEnd(CarrierRoute.Chute), 12);
            Assert.Equal(SLanding + 1.6, r.Line.SEnd(CarrierRoute.Exit), 12);
            Assert.Equal(6.15, r.Line.SReturn, 12);
        }

        /// <summary>
        /// The payload is seeded from the game clock (<c>seed = carriers · 7 + floor(game.clock · 13)</c>, L2666–L2673), so a
        /// line built after game time 0 is told the clock (U-20 DL-06: it counted from the graph's build). At 2500 s the
        /// seed is 32500 and the carrier comes with three parcels (the prototype's LCG, worked by hand from L2667–L2672; the
        /// first draw is under 0.2, so empty, for every seed below 25 555, i.e. for the first 33 minutes of a game).
        /// </summary>
        [Fact]
        public void Line_PayloadIsSeededFromTheGameClock_L2666()
        {
            var r = new LineRig();
            r.Line.Clock = 2500;
            Mech.Run(r.G, 1);
            var c = r.First;
            Assert.Equal(2500 + 1.0 / 60, r.Line.Clock);
            Assert.Equal(3, c.Parcels);
            double[,] want =
            {
                { 0.1695978482671072, 0.05819217315092318, 0.1434165933371599 },
                { 0.18702456276259596, -0.07157559119936804, 0.11615485195822772 },
                { 0.1352795820009334, -0.06762245606753158, 0.07752349506016987 },
            };
            for (int k = 0; k < 3; k++)
            {
                Assert.Equal(want[k, 0], c.ParcelSizeOf(k), 15);
                Assert.Equal(-want[k, 1], c.ParcelZOf(k), 15);                     // Unity z (three's negated)
                Assert.Equal(want[k, 2], c.ParcelYawOf(k), 15);
            }
            var fresh = new LineRig();                                           // a line left at clock 0 draws seed 0: empty
            Mech.Run(fresh.G, 1);
            Assert.Equal(0, fresh.First.Parcels);
        }

        [Fact]
        public void Line_SpawnsAtOnceWhenRunning_RisesAt0_6_DocksAndWaits3_4s_L2696_L2703()
        {
            var r = new LineRig();
            Mech.Run(r.G, 1);
            Assert.True(r.Emitted(CarrierLineEvent.Spawned));                    // lastSpawn = −100, L8032
            var c = r.First;
            Assert.Equal(CarrierState.Rise, c.State);
            Assert.Equal(0.01, c.S, 12);
            Assert.Equal(63.5, c.Position, 12);
            Assert.Equal(-0.74, c.Y, 12);
            Assert.Equal(0.6, c.VelocityY, 9);
            int dock = r.Until(() => r.Emitted(CarrierLineEvent.Docked));
            Assert.Equal(124, dock);                                             // s ≥ 1.25 − 1e-4 at step 125
            Assert.Equal(CarrierState.Dock, c.State);
            Assert.Equal(64.0, c.Position, 9);
            Assert.True(r.Line.DockLit);
            int move = r.Until(() => c.State == CarrierState.Move);
            Assert.InRange(move, 204, 205);                                     // 3.4 s
            Assert.Equal(1, r.Line.Count);
        }

        [Fact]
        public void Line_NextSpawn_Every6s_OnlyWithTheDockAndTheFirst1_4mClear_L2696()
        {
            var r = new LineRig();
            var spawns = new List<double>();
            for (int i = 0; i < 60 * 20; i++)
            {
                Mech.Run(r.G, 1);
                if (r.Emitted(CarrierLineEvent.Spawned)) spawns.Add(r.Line.Clock);
                foreach (var e in r.All(CarrierLineEvent.Spawned))
                    for (int k = 0; k < r.Line.Count; k++)
                        if (r.Line.At(k).Seq != e.Index) Assert.True(r.Line.At(k).S >= 1.4 && r.Line.At(k).State != CarrierState.Dock);
            }
            Assert.True(spawns.Count >= 3);
            for (int k = 1; k < spawns.Count; k++) Assert.True(spawns[k] - spawns[k - 1] > 6.0);
        }

        [Fact]
        public void Line_StoppedBelt_NoSpawn_DockWaitHolds_CarriersStand_L2696_L2702_L2705()
        {
            var r = new LineRig(running: false);
            Mech.Run(r.G, 600);
            Assert.Equal(0, r.Line.Count);
            r.Belt.Engaged = true;
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Dock);
            r.Belt.Engaged = false;
            Mech.Run(r.G, 600);
            Assert.Equal(CarrierState.Dock, c.State);
            Assert.Equal(3.4, c.Wait, 9);
            r.Belt.Engaged = true;
            r.Until(() => c.State == CarrierState.Move);
            Mech.Run(r.G, 60);
            r.Belt.Engaged = false;
            double s = c.S;
            Mech.Run(r.G, 120);
            Assert.Equal(s, c.S);
            Assert.Equal(0, c.VelocityX);
            Assert.Equal(CarrierLineState.Stopped, r.Line.State);
        }

        [Fact]
        public void Line_Junction_TakesThePointsAsItPasses_L2709()
        {
            var r = new LineRig(exit: false);
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.S > 4.0);
            r.Points.Engaged = true;                                             // thrown before it reaches 4.85
            r.Until(() => r.Emitted(CarrierLineEvent.Junction));
            Assert.Equal(CarrierRoute.Exit, c.Route);
            Assert.Equal((int)CarrierRoute.Exit, (int)r.All(CarrierLineEvent.Junction)[0].Value);
            r.Points.Engaged = false;                                            // too late for this one
            Mech.Run(r.G, 120);
            Assert.Equal(CarrierRoute.Exit, c.Route);
            Assert.True(c.Y > 0);                                                // up the ramp blade
        }

        [Fact]
        public void Line_Chute_TipsAt69_5_DumpsAt0_35s_BangsAt0_5_BackToTheReturnLift_Sinks_L2728_L2747()
        {
            var r = new LineRig();
            Mech.Run(r.G, 1);
            var c = r.First;
            int seq = c.Seq, parcels = c.Parcels;
            r.Until(() => r.Emitted(CarrierLineEvent.Tip));
            Assert.Equal(CarrierState.Tip, c.State);
            Assert.Equal(69.5, c.Position, 9);
            Assert.Equal(CarrierRoute.Chute, c.Route);
            var player = new PlayerPose(68.0, 0);
            int dump = -1, bang = -1;
            for (int i = 1; i <= 130 && c.State == CarrierState.Tip; i++)
            {
                Mech.Run(r.G, 1, player);
                if (r.Emitted(CarrierLineEvent.PayloadDumped)) dump = i;
                if (r.Emitted(CarrierLineEvent.Startle)) bang = i;
                if (i == 42) Assert.Equal(-68 * Math.PI / 180, c.TipRad, 9);    // fully over between 0.7 and 1.6 s
            }
            if (parcels > 0) Assert.Equal(22, dump); else Assert.Equal(-1, dump);
            Assert.Equal(31, bang);                                              // t > 0.5
            Assert.Equal(CarrierState.Back, c.State);
            int back = r.Until(() => c.State == CarrierState.Sink);
            Assert.InRange(back, 72, 73);                                        // 0.6 m at 0.5 m/s
            Assert.Equal(68.9, c.Position, 9);
            int gone = r.Until(() => r.Emitted(CarrierLineEvent.Removed));
            Assert.InRange(gone, 118, 119);                                      // 0.3 s, then 1 m at 0.6 m/s
            Assert.Null(r.Line.FindBySeq(seq));
        }

        [Fact]
        public void Line_ChuteBang_DoesNotStartleHimUpOnTheGallery_L2735()
        {
            var r = new LineRig();
            Mech.Run(r.G, 1);
            r.Until(() => r.Emitted(CarrierLineEvent.Tip));
            Mech.Run(r.G, 60, new PlayerPose(74.0, 1.6));
            Assert.False(r.Emitted(CarrierLineEvent.Startle));
        }

        [Fact]
        public void Line_Exit_UnriddenRunsToTheReturnAndSinksFromTheGallery_L2716()
        {
            var r = new LineRig(exit: true);
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Sink);
            Assert.Equal(74.3, c.Position, 9);
            Assert.Equal(1.6, c.Y, 9);
            Mech.Run(r.G, 18);
            Assert.Equal(1.6, c.Y, 9);                                           // 0.3 s before the lift drops
            Mech.Run(r.G, 1);
            Assert.True(c.Y < 1.6);
            Assert.True(r.Until(() => r.Emitted(CarrierLineEvent.Removed)) > 0);
        }

        [Fact]
        public void Dock_Dl06Dock_IsTheLinesDockPhase_HeldOnlyWhileHisHopTargetsIt_L2693_L2704()
        {
            var r = new LineRig();
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => r.Emitted(CarrierLineEvent.Docked));
            Assert.Equal(3.4, c.Wait, 12);                                       // DOCK_WAIT, L2461
            Assert.True(r.Line.DockLit);
            Mech.Run(r.G, 60);
            double w = c.Wait;
            Assert.Equal(3.4 - 1.0, w, 9);
            r.Line.BeginBoard(c);                                                // the board act targets it: the wait holds
            Mech.Run(r.G, 120);
            Assert.Equal(w, c.Wait);
            Assert.Equal(CarrierState.Dock, c.State);
            r.Line.BeginBoard(null);                                             // the hop is over without mounting
            int move = r.Until(() => c.State == CarrierState.Move);
            Assert.InRange(move, 143, 145);                                      // the rest of the 3.4 s
            Assert.False(r.Line.DockLit);
        }

        // ---- Riding -----------------------------------------------------------------------------------------------------

        [Fact]
        public void Ride_BoardAtTheDock_HoldsTheWait_RideSyncFollows_UnloadsAtTheLanding_L2702_L2710_L2950_L2961()
        {
            var r = new LineRig(exit: true);
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Dock);
            Mech.Run(r.G, 200);                                                  // wait almost run out
            Assert.Same(c, r.Line.FindBoardable(64.3));
            Assert.Null(r.Line.FindBoardable(64.6));
            r.Line.BeginBoard(c);                                                // the hop: the wait holds
            double w = c.Wait;
            Mech.Run(r.G, 30);
            Assert.Equal(w, c.Wait);
            r.Line.Mount(c);
            Mech.Run(r.G, 1);
            Assert.True(c.Ridden);
            Assert.Same(c, r.Line.Ride);
            Assert.InRange(c.Wait, 0.9 - 1.0 / 60 - 1e-9, 0.9);                  // max(wait, 0.9), L2950
            r.Until(() => c.State == CarrierState.Move);
            Mech.Run(r.G, 30);
            Assert.Equal(0.6, c.VelocityX, 9);
            Assert.Equal(c.Y + 0.14, c.RideY, 12);
            Assert.Equal(c.Position, ((IPositionSource)c).Position);
            r.Until(() => r.Emitted(CarrierLineEvent.Unload));
            Assert.Equal(CarrierState.Unload, c.State);
            Assert.Equal(72.7, c.Position, 9);
            Assert.Equal(1.6 + 0.14, c.RideY, 9);
            Mech.Run(r.G, 300);
            Assert.Equal(CarrierState.Unload, c.State);                          // waits while he is aboard
            r.Line.Alight();
            Mech.Run(r.G, 1);
            Assert.Null(r.Line.Ride);
            int on = r.Until(() => c.State == CarrierState.Move);
            Assert.Equal(59, on);                                                // c.t > 1.0 on the 60th step he is off (incl. the one above): 60 × 1/60 sums to 1.0000000000000013, L2719
        }

        [Fact]
        public void Ride_ToTheChute_TipsHimOutWithThePost_L2733()
        {
            var r = new LineRig();
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Dock);
            r.Line.Mount(c);
            r.Until(() => r.Emitted(CarrierLineEvent.Tip));
            Assert.True(c.Ridden);
            int tipped = r.Until(() => r.Emitted(CarrierLineEvent.RiderTipped));
            Assert.Equal(22, tipped);
            Assert.False(c.Ridden);
            Assert.Null(r.Line.Ride);
        }

        [Fact]
        public void Ride_QueuesKeep0_8Apart_BehindARiddenCarrierAtTheLanding_L2707()
        {
            var r = new LineRig(exit: true);
            Mech.Run(r.G, 1);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Dock);
            r.Line.Mount(c);
            r.Until(() => r.Line.Count >= 2 && r.Line.At(1).S > SLanding - 2);
            var d = r.Line.At(1);
            Mech.Run(r.G, 600);
            Assert.Equal(CarrierState.Unload, c.State);
            Assert.Equal(SLanding - 0.8, d.S, 9);
            Assert.Equal(CarrierState.Move, d.State);
        }

        // ---- Loads (DL-07's weights) -------------------------------------------------------------------------------

        private static (LineRig r, TestItem w0, TestItem w1) Loaded(bool exit)
        {
            var r = new LineRig(exit: exit);
            var w0 = new TestItem(); var w1 = new TestItem();
            r.Line.SetLoadItems(w0, w1);
            Mech.Run(r.G, 1);
            r.Until(() => r.First.State == CarrierState.Dock);
            return (r, w0, w1);
        }

        private static InteractionQuery At(double x, double y = 0) => new InteractionQuery(x, y, 0, 1, true, false, HoldKind.Item, null, null);

        [Fact]
        public void Load_TwoWeightsPerTub_AtTheDock_L4441_L4452_L4979_L4989()
        {
            var (r, w0, w1) = Loaded(false);
            var loader = r.Line.Loader;
            Assert.True(loader.Offer(At(64.5), out var pose));
            Assert.Equal(64.0, pose.StandX);
            Assert.True(loader.IsAvailable(At(64.0 + 0.69)));                    // reach 0.7 at the dock
            Assert.False(loader.IsAvailable(At(64.0 - 0.71)));
            Assert.False(loader.IsAvailable(At(64.75)));
            Assert.False(loader.IsAvailable(At(64.0, 1.6)));                     // up on the gallery
            Assert.True(loader.Accepts(w0));
            Assert.False(loader.Accepts(new TestItem()));
            loader.IsAvailable(At(64.2));
            loader.OnPlaced(w0);
            Mech.Run(r.G, 1);
            Assert.True(r.Emitted(CarrierLineEvent.LoadPlaced));
            Assert.Equal(1, r.First.Load1);
            Assert.True(r.First.ParcelsHidden);
            loader.IsAvailable(At(64.2));
            loader.OnPlaced(w1);
            Mech.Run(r.G, 1);
            Assert.Equal(2, r.First.Load2);
            Assert.False(loader.IsAvailable(At(64.2)));                          // full
        }

        [Fact]
        public void Load_WhileStopped_AnyEmptyCarrierBesideHim_StandsAtIt_L4985()
        {
            var (r, _, _) = Loaded(false);
            var c = r.First;
            r.Until(() => c.State == CarrierState.Move);
            Mech.Run(r.G, 60);
            Assert.False(r.Line.Loader.IsAvailable(At(c.Position)));            // moving with the belt on
            r.Belt.Engaged = false;
            Mech.Run(r.G, 1);
            Assert.True(r.Line.Loader.Offer(At(c.Position + 0.5), out var pose));
            Assert.Equal(c.Position, pose.StandX);
            Assert.True(r.Line.Loader.IsAvailable(At(c.Position - 0.59)));        // reach 0.6 beside a moving one
            Assert.False(r.Line.Loader.IsAvailable(At(c.Position + 0.65)));
        }

        [Fact]
        public void Load_CarrierGoneBeforeTheRelease_IsRefused_L4453()
        {
            var (r, w0, _) = Loaded(true);
            var c = r.First;
            Assert.True(r.Line.Loader.IsAvailable(At(64.0)));
            r.Until(() => c.State == CarrierState.Move);
            r.Until(() => c.Route != CarrierRoute.None);
            r.Until(() => c.State == CarrierState.Sink);
            r.Line.Loader.OnPlaced(w0);
            Mech.Run(r.G, 1);
            Assert.True(r.Emitted(CarrierLineEvent.LoadRefused));
        }

        [Fact]
        public void Load_UpTheRamp_TipsIntoTheBucketAtTheLanding_SecondWeight0_18sLater_L2711_L2722_L4992()
        {
            var (r, w0, w1) = Loaded(true);
            var c = r.First;
            r.Line.Loader.IsAvailable(At(64.0)); r.Line.Loader.OnPlaced(w0); Mech.Run(r.G, 1);
            r.Line.Loader.IsAvailable(At(64.0)); r.Line.Loader.OnPlaced(w1); Mech.Run(r.G, 1);
            r.Until(() => c.State == CarrierState.TipLoad);
            Assert.Equal(72.7, c.Position, 9);
            var got = new List<(int code, int step)>();
            for (int i = 1; i <= 120; i++)
            {
                Mech.Run(r.G, 1);
                foreach (var e in r.All(CarrierLineEvent.LoadToBucket)) got.Add((e.Index, i));
                if (i == 36) Assert.Equal(62 * Math.PI / 180, c.TipRad, 9);
            }
            Assert.Equal(2, got.Count);
            Assert.Equal((1, 25), got[0]);                                        // t > 0.4
            Assert.Equal(2, got[1].code);
            Assert.InRange(got[1].step - got[0].step, 10, 11);                   // 0.18 s
            Assert.Equal(CarrierState.Move, c.State);                           // on at t > 1.8
            Assert.Equal(0, c.TipRad);
        }

        [Fact]
        public void Load_DownTheChute_IsLost_BackIn4s_L2734_L5004()
        {
            var (r, w0, _) = Loaded(false);
            r.Line.Loader.IsAvailable(At(64.0)); r.Line.Loader.OnPlaced(w0);
            r.Until(() => r.Emitted(CarrierLineEvent.LoadLost));
            var e = r.All(CarrierLineEvent.LoadLost)[0];
            Assert.Equal(1, e.Index);
            Assert.Equal(4, e.Value);
            Assert.False(r.Emitted(CarrierLineEvent.LoadToBucket));
        }

        // ---- Payload, reset, snapshot ----------------------------------------------------------------------------------

        [Fact]
        public void Payload_IsTheClockSeededLcg_L2666_L2673()
        {
            var r = new LineRig("scanned", running: false);
            Mech.Run(r.G, 437);                                                  // the clock at 437/60 s
            r.Belt.Engaged = true;
            Mech.Run(r.G, 1);
            double clock = r.Line.Clock;
            long seed = 0 * 7 + (long)Math.Floor(clock * 13);
            double Rnd() { seed = (seed * 16807 + 11) % 2147483647; return seed / 2147483647.0; }
            int n = Rnd() < 0.2 ? 0 : 1 + (int)Math.Floor(Rnd() * 2.2);
            var c = r.First;
            Assert.Equal(n, c.Parcels);
            for (int k = 0; k < n; k++)
            {
                Assert.Equal(0.12 + Rnd() * 0.08, c.ParcelSizeOf(k), 12);
                Assert.Equal(-(Rnd() - 0.5) * 0.15, c.ParcelZOf(k), 12);
                Assert.Equal((Rnd() - 0.5) * 0.6, c.ParcelYawOf(k), 12);
            }
        }

        [Theory]
        [InlineData("hatch", false, false)] [InlineData("scanned", true, false)] [InlineData("landing", true, true)]
        public void Reset_ClearsTheLine_SpawnsAtOnceIfTheBeltRuns_L8030_L8032(string cp, bool running, bool exit)
        {
            var r = new LineRig("scanned");
            Mech.Run(r.G, 900);
            Assert.True(r.Line.Count > 0);
            r.Belt.Engaged = running; r.Points.Engaged = exit;                  // the levers are reset first in a scene
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(0, r.Line.Count);
            Assert.Null(r.Line.Ride);
            Mech.Run(r.G, 1);
            Assert.Equal(running ? 1 : 0, r.Line.Count);
            Assert.Equal(exit ? CarrierRoute.Exit : CarrierRoute.Chute, r.Line.Route);
        }

        [Fact]
        public void Line_RestoredWithCarriersInEveryPhase_ContinuesBitIdentically()
        {
            var a = new LineRig();
            var (w0, w1) = (new TestItem(), new TestItem());
            a.Line.SetLoadItems(w0, w1);
            for (int i = 0; i < 60 * 25; i++)
            {
                if (i == 400) a.Points.Engaged = true;
                if (i == 900) a.Points.Engaged = false;
                Mech.Run(a.G, 1, new PlayerPose(68.5, 0));
            }
            Assert.True(a.Line.Count >= 3);
            var b = new LineRig("landing", running: false);
            b.Line.SetLoadItems(w0, w1);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int i = 0; i < 60 * 30; i++)
            {
                if (i == 300) { a.Points.Engaged = b.Points.Engaged = true; }
                Mech.Run(a.G, 1, new PlayerPose(68.5, 0));
                Mech.Run(b.G, 1, new PlayerPose(68.5, 0));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
        }

        // ---- The stop lever and the points ------------------------------------------------------------------------------

        private sealed class LeverRig
        {
            public readonly TestSource Scanner;
            public readonly PointsLever Stop, Points;
            public readonly MechanismGraph G;

            public LeverRig(string cp, bool scanned)
            {
                Scanner = new TestSource("dl06.scanner") { Engaged = scanned };
                Stop = new PointsLever("dl06.stopLever", PointsLeverParams.Dl06StopLever());
                Points = new PointsLever("dl06.points", PointsLeverParams.Dl06Points());
                G = Mech.Graph(cp, Scanner, Stop, Points);
            }
        }

        [Theory]
        [InlineData("hatch", false, false)] [InlineData("scanned", true, false)] [InlineData("landing", true, true)]
        [InlineData("tunnel", true, true)] [InlineData("forwarded", true, true)] [InlineData("school", true, false)]
        public void Levers_ResetFromCheckpoint_L8032_L8034(string cp, bool running, bool exit)
        {
            var r = new LeverRig(cp, running);
            Assert.Equal(running, r.Stop.Engaged);
            Assert.Equal(exit, r.Points.Engaged);
            Assert.Equal(running ? -18 : 6, r.Stop.LeverDeg);
            Assert.Equal(exit ? 6 : -18, r.Points.LeverDeg);
        }

        [Fact]
        public void StopLever_StartsWhenTheScanIsDone_AndOnlyThenAnswers_L2815_L2867()
        {
            var r = new LeverRig("hatch", false);
            var q = new InteractionQuery(62.5, 0, 0, 1, true, false, HoldKind.None, null, null);
            Assert.False(r.Stop.IsAvailable(q));
            Assert.False(r.Points.IsAvailable(q));
            Mech.Run(r.G, 10);
            Assert.Equal(PointsLeverState.Off, r.Stop.State);
            r.Scanner.Engaged = true;
            Mech.Run(r.G, 1);
            Assert.True(Mech.Emitted(r.G, "dl06.stopLever", PointsLeverEvent.AutoStart));
            Assert.Equal(PointsLeverState.On, r.Stop.State);
            Assert.Equal(PointsLeverState.Off, r.Points.State);
            Assert.True(r.Stop.IsAvailable(q));
            Assert.Equal(-0.11, r.Stop.Station.StandZ, 12);
            Mech.Run(r.G, 10);
            Assert.False(Mech.Emitted(r.G, "dl06.stopLever", PointsLeverEvent.AutoStart));
        }

        [Fact]
        public void StopLever_TogglesAtLeverPullF22_EndsAtF33_L2925_L2932()
        {
            var r = new LeverRig("scanned", true);
            Assert.Equal("LeverPull", r.Stop.Profile.Clip);
            int thrown = -1;
            int steps = Mech.PlayAct(r.G, r.Stop, onStep: (k, f) =>
            {
                if (Mech.Emitted(r.G, "dl06.stopLever", PointsLeverEvent.Thrown)) { thrown = k; Assert.InRange(f, 22, 22.4 + 1e-9); }
                if (f > 10 && f < 22) Assert.InRange(r.Stop.LeverDeg, -18, 6);
            });
            Assert.True(thrown > 0);
            Assert.Equal(PointsLeverState.Off, r.Stop.State);                    // the belt stops
            Assert.Equal(83, steps);                                             // f33 = step 82.5 → 83
            Assert.Equal(6, r.Stop.LeverDeg, 9);
        }

        [Fact]
        public void Points_StuckWhileTheBeltRuns_ClunksTwice_EndsAtF45_NoChange_L2910_L2919()
        {
            var r = new LeverRig("scanned", true);
            Assert.Equal("LeverStuck", r.Points.Profile.Clip);
            var clunks = new List<double>();
            int steps = Mech.PlayAct(r.G, r.Points, onStep: (k, f) =>
            {
                foreach (var e in Mech.Events(r.G))
                    if (e.Id == "dl06.points" && e.Kind == MechanismEventKind.Event && e.Code == (int)PointsLeverEvent.Clunk) clunks.Add(f);
            });
            Assert.Equal(2, clunks.Count);
            Assert.InRange(clunks[0], 12, 12.4 + 1e-9);
            Assert.InRange(clunks[1], 21, 21.4 + 1e-9);
            Assert.Equal(113, steps);                                            // f45
            Assert.Equal(PointsLeverState.Off, r.Points.State);
            Assert.False(Mech.Emitted(r.G, "dl06.points", PointsLeverEvent.Thrown));
        }

        /// <summary>
        /// The lever stands where it has eased to (<c>game.stopLever</c>: rate 8 toward its angle, L2833), and a pull swings
        /// from there (<c>a.from = game.stopLever</c>, taken on the step the clip starts, before that step's ease; L2911), not
        /// from its rest angle: just after the belt started, the stop lever still stands near 6° on its way to −18°.
        /// </summary>
        [Fact]
        public void Levers_EaseTowardTheirAngle_AndAPullSwingsFromWhereItStands_L2833_L2911()
        {
            var r = new LeverRig("hatch", false);
            Assert.Equal(6, r.Stop.ViewDeg);
            r.Scanner.Engaged = true;
            Mech.Run(r.G, 1);                                                    // startBelt: On, the lever starts toward −18
            double k = 8.0 / 60, v1 = 6 + (-18 - 6) * k;
            Assert.Equal(-18, r.Stop.LeverDeg);
            Assert.Equal(v1, r.Stop.ViewDeg, 12);
            Mech.Run(r.G, 1);                                                    // the clip's step: #4 reads v1, #6 eases on
            Assert.Equal(v1 + (-18 - v1) * k, r.Stop.ViewDeg, 12);
            double first = double.NaN;
            Mech.PlayAct(r.G, r.Stop, onStep: (s, f) => { if (s == 1) first = r.Stop.LeverDeg; });
            Assert.Equal(v1, first, 12);                                         // from + (to − from) · smooth((0.4 − 10) / 12) = from
            Assert.Equal(PointsLeverState.Off, r.Stop.State);                    // from 2.8° > −6° it swings to −18° (L2911); the throw stops the belt
            Assert.Equal(6, r.Stop.LeverDeg);                                    // leverHold = null at f33: the rest angle
            for (int i = 0; i < 600; i++) Mech.Run(r.G, 1);
            Assert.Equal(6, r.Stop.ViewDeg, 9);
        }

        [Fact]
        public void Points_WithTheBeltStopped_ThrowToTheExit_RouteShot_Proud_L2907_L2933()
        {
            var r = new LeverRig("scanned", true);
            Mech.PlayAct(r.G, r.Stop);
            Mech.Run(r.G, 1);
            Assert.False(r.Stop.Engaged);
            Assert.Equal("LeverPull", r.Points.Profile.Clip);
            bool shot = false, proud = false;
            Mech.PlayAct(r.G, r.Points, onStep: (k, f) =>
            {
                shot |= Mech.Emitted(r.G, "dl06.points", PointsLeverEvent.RouteShot);
                proud |= Mech.Emitted(r.G, "dl06.points", PointsLeverEvent.Proud);
            });
            Assert.True(r.Points.Engaged);
            Assert.True(shot);
            Assert.True(proud);
            Mech.PlayAct(r.G, r.Points, onStep: (k, f) => Assert.False(Mech.Emitted(r.G, "dl06.points", PointsLeverEvent.Proud)));
            Assert.False(r.Points.Engaged);                                       // back to the chute: no Proud
        }

        [Fact]
        public void Levers_RestoredMidPull_ContinueBitIdentically()
        {
            var a = new LeverRig("scanned", true);
            Mech.PlayAct(a.G, a.Stop, max: 20);
            var b = new LeverRig("hatch", false);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            Mech.PlayAct(a.G, a.Stop, startStep: 21);
            Mech.PlayAct(b.G, b.Stop, startStep: 21);
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            Assert.Equal(PointsLeverState.Off, b.Stop.State);
        }

        // ---- DL-08's returns belt ---------------------------------------------------------------------------------------

        private sealed class BeltRig
        {
            public readonly TestSource Pawl;
            public readonly ReturnsBelt Belt;
            public readonly MechanismGraph G;

            public BeltRig(string cp = "latched", bool pawl = true)
            {
                Pawl = new TestSource("dl08.pawl") { Engaged = pawl };
                Belt = new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt());
                G = Mech.Graph(cp, Pawl, Belt);
            }

            public bool Emitted(ReturnsBeltEvent e) => Mech.Emitted(G, "dl08.belt", e);
        }

        private static readonly PlayerPose OnDeckAway = new PlayerPose(89.5, 1.6);

        [Fact]
        public void Belt_WarnsWhenHePassesTheShaftWithThePawlSet_BellsAt0_0_9_1_8_KlaxonAt2_7_L3218_L3224_L3420()
        {
            var r = new BeltRig(pawl: false);
            Mech.Run(r.G, 30, OnDeckAway);
            Assert.Equal(ReturnsBeltState.Idle, r.Belt.State);                   // no pawl, no belt
            r.Pawl.Engaged = true;
            Mech.Run(r.G, 30, new PlayerPose(88.8, 1.6));                        // not yet past SHAFT.x1 + 0.6
            Mech.Run(r.G, 30, new PlayerPose(89.0, 1.6, busy: true));            // in an act
            Mech.Run(r.G, 30, Mech.Pose(89.0, 1.9, grounded: false));            // in the air (L3418)
            Mech.Run(r.G, 30, Mech.Pose(89.0, 1.6, holding: true));              // pushing the trolley (L3416)
            Assert.Equal(ReturnsBeltState.Idle, r.Belt.State);
            var bells = new List<int>();
            int klaxon = -1;
            for (int i = 1; i <= 200; i++)
            {
                Mech.Run(r.G, 1, OnDeckAway);
                if (r.Emitted(ReturnsBeltEvent.Bell)) bells.Add(i);
                if (r.Emitted(ReturnsBeltEvent.Klaxon)) klaxon = i;
            }
            Assert.Equal(new List<int> { 1, 55, 109 }, bells);
            Assert.Equal(163, klaxon);                                           // t > 2.7
            Assert.Equal(ReturnsBeltState.Run, r.Belt.State);
        }

        [Fact]
        public void Belt_Crates_SlideDownTheChute_RideTheBelt_TurnOutThroughTheFlaps_L3150_L3164()
        {
            var r = new BeltRig("cage");
            Assert.Equal(ReturnsBeltState.Run, r.Belt.State);
            int spawn = Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateSpawned), 100, OnDeckAway);
            Assert.InRange(spawn, 30, 31);                                       // next 0.5 after a reset
            var c = r.Belt.At(0);
            Assert.Equal(CrateState.Chute, c.State);
            int land = Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateLanded), 100, OnDeckAway);
            Assert.InRange(land, 44, 45);                                        // 0.75 s
            Assert.Equal(97.25, c.X, 9);
            Assert.Equal(1.6, c.Y, 12);
            Assert.Equal(0, c.Z, 12);
            Mech.Run(r.G, 60, OnDeckAway);
            Assert.Equal(97.25 - 0.32, c.X, 9);
            Mech.RunUntil(r.G, () => c.State == CrateState.Turn, 3000, OnDeckAway);
            Assert.True(c.X - c.Half <= 91.0 + 1e-9);
            Assert.InRange(c.X - c.Half, 91.0 - 0.32 / 60 - 1e-9, 91.0);
            int gone = Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateGone), 200, OnDeckAway);
            Assert.Equal(88, gone);                                              // t > 1.45
        }

        [Fact]
        public void Belt_SpawnSpacing_2_9To4_2s_ClearOfTheChute_1_25BehindTheLast_L3141_L3144()
        {
            var r = new BeltRig("cage");
            var times = new List<int>();
            for (int i = 1; i <= 60 * 120; i++)
            {
                Mech.Run(r.G, 1, OnDeckAway);
                if (r.Emitted(ReturnsBeltEvent.CrateSpawned))
                {
                    times.Add(i);
                    Assert.InRange(r.Belt.Next, 2.9, 4.2);
                    for (int k = 0; k < r.Belt.Count - 1; k++) Assert.True(r.Belt.At(k).State != CrateState.Chute);
                }
            }
            Assert.True(times.Count > 20);
            // the last crate must be 1.25 down the belt: 0.75 s down the chute + 1.25 / 0.32 s, at least 4.66 s apart
            for (int k = 1; k < times.Count; k++) Assert.InRange((times[k] - times[k - 1]) / 60.0, 0.75 + 1.25 / 0.32, 4.2 + 1.0 / 60 + 0.75 + 1.25 / 0.32);
            // standing at the chute's foot holds the next crate back
            var b = new BeltRig("cage");
            Mech.Run(b.G, 600, new PlayerPose(97.0, 1.6));
            Assert.Equal(0, b.Belt.Count);
            Mech.Run(b.G, 600, new PlayerPose(97.0, 2.2));                       // up off the deck: clear
            Assert.True(b.Belt.Count > 0);
        }

        [Fact]
        public void Belt_CrateOdds_55_30_15_L3130()
        {
            var r = new BeltRig("cage");
            int[] n = new int[3];
            for (int i = 0; i < 60 * 60 * 30; i++)
            {
                Mech.Run(r.G, 1, OnDeckAway);
                foreach (var e in Mech.Events(r.G))
                    if (e.Kind == MechanismEventKind.Event && e.Code == (int)ReturnsBeltEvent.CrateSpawned) n[e.Index]++;
            }
            double total = n[0] + n[1] + n[2];
            Assert.True(total > 300);
            Assert.InRange(n[0] / total, 0.49, 0.61);
            Assert.InRange(n[1] / total, 0.24, 0.36);
            Assert.InRange(n[2] / total, 0.10, 0.20);
        }

        [Fact]
        public void Belt_CarriesHimBack_AndCratesAreSolidInTheLane_L1733_L3439()
        {
            var r = new BeltRig("cage");
            Assert.Equal(-0.32, r.Belt.CarryVelocity(94.0));
            Assert.Equal(0, r.Belt.CarryVelocity(90.5));
            Assert.Equal(0, r.Belt.CarryVelocity(97.7));
            var idle = new BeltRig("latched");
            Assert.Equal(0, idle.Belt.CarryVelocity(94.0));
            Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateSpawned), 100, OnDeckAway);
            var c = r.Belt.At(0);
            Assert.Equal(1.6, r.Belt.SurfaceAt(97.25, 1.6));                     // on the chute: not solid yet
            Mech.RunUntil(r.G, () => c.State == CrateState.Belt, 100, OnDeckAway);
            Assert.Equal(1.6 + c.Height, r.Belt.SurfaceAt(c.X + c.Half - 1e-6, 1.6), 12);
            Assert.Equal(1.6, r.Belt.SurfaceAt(c.X + c.Half + 0.01, 1.6));
        }

        [Theory]
        [InlineData("goods", ReturnsBeltState.Idle)] [InlineData("latched", ReturnsBeltState.Idle)]
        [InlineData("cage", ReturnsBeltState.Run)] [InlineData("tunnel", ReturnsBeltState.Run)]
        public void Belt_ResetFromCheckpoint_L8045(string cp, ReturnsBeltState state)
        {
            var r = new BeltRig("cage");
            Mech.Run(r.G, 900, OnDeckAway);
            Assert.True(r.Belt.Count > 0);
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(state, r.Belt.State);
            Assert.Equal(0, r.Belt.Count);
            Assert.Equal(0.5, r.Belt.Next);
        }

        [Fact]
        public void Belt_RestoredMidRun_ContinuesBitIdentically_AndRunsAreDeterministic()
        {
            var a = new BeltRig("cage");
            Mech.Run(a.G, 60 * 17, OnDeckAway);
            Assert.True(a.Belt.Count >= 2);
            var b = new BeltRig("goods", pawl: false);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            var c = new BeltRig("cage");
            Mech.Run(c.G, 60 * 17, OnDeckAway);
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(c.G));
            for (int i = 0; i < 60 * 30; i++)
            {
                Mech.Run(a.G, 1, OnDeckAway);
                Mech.Run(b.G, 1, OnDeckAway);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
        }

        /// <summary>
        /// A replay can feed the crates' draws (the prototype's come from the page's shared Math.random): a spawn takes the
        /// type's, the spin's and the next interval's, in that order (L3130, L3134, L3144); the belt's own generator is untouched.
        /// </summary>
        [Fact]
        public void Belt_Draws_CanBeFed_TypeSpinNext_L3130_L3134_L3144()
        {
            var r = new BeltRig("cage");
            var fed = new Queue<double>(new[] { 0.9, 0.75, 0.5 });
            r.Belt.Draws = () => fed.Dequeue();
            int spawn = Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateSpawned), 100, OnDeckAway);
            Assert.True(spawn > 0);
            Assert.Empty(fed);
            var c = r.Belt.At(0);
            Assert.Equal(2, c.Type);                                                // r ≥ 0.85: tall
            Assert.Equal((0.75 - 0.5) * 0.4, c.Spin, 15);
            Assert.Equal(2.9 + 0.5 * 1.3, r.Belt.Next, 15);
            var own = new BeltRig("cage");
            Mech.RunUntil(own.G, () => own.Emitted(ReturnsBeltEvent.CrateSpawned), 100, OnDeckAway);
            r.Belt.Draws = null;                                                    // back to its own generator, unconsumed
            Mech.RunUntil(r.G, () => r.Emitted(ReturnsBeltEvent.CrateSpawned), 400, OnDeckAway);
            Assert.Equal(own.Belt.At(0).Type, r.Belt.At(1).Type);
            Assert.Equal(own.Belt.At(0).Spin, r.Belt.At(1).Spin);
        }
    }
}
