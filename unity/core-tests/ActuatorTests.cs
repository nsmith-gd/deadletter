using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Follower gates, cranks and doors (§4.13a follower law, §4.13d).</summary>
    public class ActuatorTests
    {
        private const double Dt = Mech.Dt;
        private const double GateX = 30.6;

        private static (MechanismGraph g, FollowerActuator gate, TestSource plate) Dl03(double load, string cp = "weighroom")
        {
            var plate = new TestSource("dl03.plate") { Load = load };
            var gate = new FollowerActuator("dl03.gate", FollowerParams.Dl03Gate());
            return (Mech.Graph(cp, plate, gate), gate, plate);
        }

        // ---- FollowerActuator -----------------------------------------------------------------------------------------------

        [Fact]
        public void Follower_RisesAt0_55_ToLoadTimes1_2_TickingEvery5cm_L2381_L2382()
        {
            var (g, gate, plate) = Dl03(0);
            plate.Load = 1;
            Mech.Run(g, 60);
            Assert.Equal(0.55, gate.Position, 9);
            Assert.Equal(FollowerState.Rising, gate.State);
            var ticks = new List<double>();
            int n = Mech.RunUntil(g, () =>
            {
                if (Mech.Emitted(g, "dl03.gate", FollowerEvent.Tick)) ticks.Add(gate.Position);
                return gate.Position >= 1.2;
            });
            Assert.Equal(131 - 60, n);
            Assert.Equal(1.2, gate.Position);
            for (int i = 1; i < ticks.Count; i++) Assert.InRange(ticks[i] - ticks[i - 1], 0.05, 0.06);
            Mech.Run(g, 1);
            Assert.True(Mech.Entered(g, "dl03.gate", FollowerState.Still));
        }

        [Fact]
        public void Follower_PartialLoad_HoldsAtLoadTimesOpenHeight_L2380()
        {
            var (g, gate, plate) = Dl03(0);
            plate.Load = 0.42 + 0.3;                              // weight on the trolley on the plate (LOAD, L324)
            Mech.Run(g, 200);
            Assert.Equal(0.72 * 1.2, gate.Position, 12);
            plate.Load = 2.0;                                     // capped at 1
            Mech.Run(g, 200);
            Assert.Equal(1.2, gate.Position, 12);
        }

        [Fact]
        public void Follower_FallsWithAccel9UpTo3_2_AndSlams_L2384_L2386()
        {
            var (g, gate, plate) = Dl03(1);
            Assert.Equal(1.2, gate.Position);
            plate.Load = 0;
            double slam = -1;
            int n = Mech.RunUntil(g, () =>
            {
                foreach (var e in Mech.Events(g)) if (e.Code == (int)FollowerEvent.Slam && e.Kind == MechanismEventKind.Event) slam = e.Value;
                return gate.Position <= 0;
            });
            Assert.Equal(33, n);                                  // 21 steps accelerating (0.15 m/s per step), then 12 at 3.2
            Assert.Equal(3.2, slam, 12);
            Assert.Equal(0, gate.Velocity);
        }

        [Fact]
        public void Follower_ShortDrop_LandsWithoutSlam_L2385()
        {
            var (g, gate, plate) = Dl03(0.02 / 1.2);
            plate.Load = 0;
            int n = Mech.RunUntil(g, () => { Assert.False(Mech.Emitted(g, "dl03.gate", FollowerEvent.Slam)); return gate.Position <= 0; });
            Assert.Equal(4, n);                                   // lands at 0.6 m/s < 0.8
        }

        [Theory]
        [InlineData(false, 0.76 + 0.03)]
        [InlineData(true, 0.58 + 0.03)]
        public void Follower_NeverComesDownOntoHim_L2392(bool crouched, double stopsAt)
        {
            var (g, gate, plate) = Dl03(1);
            plate.Load = 0;
            Mech.Run(g, 120, Mech.Pose(GateX + 0.2, 0, crouched));
            Assert.Equal(stopsAt, gate.Position, 12);
            Mech.Run(g, 60, Mech.Pose(GateX + 0.24));            // stepped out from under it: it drops
            Assert.Equal(0, gate.Position);
        }

        [Theory]
        [InlineData(2.7, false, true)]
        [InlineData(2.7, true, false)]
        [InlineData(2.9, false, false)]
        public void Follower_SlamStartlesHimNearby_UnlessBusy_L2387(double dx, bool busy, bool startled)
        {
            var (g, gate, plate) = Dl03(1);
            plate.Load = 0;
            bool seen = false;
            Mech.RunUntil(g, () => { seen |= Mech.Emitted(g, "dl03.gate", FollowerEvent.Startle); return gate.Position <= 0; },
                pose: Mech.Pose(GateX - dx, 0, false, busy));
            Assert.Equal(startled, seen);
        }

        [Fact]
        public void Follower_Dl12Gate_RisesAt0_5_Silently_NoStartle_L5402_L5405()
        {
            var strip = new TestSource("dl12.strip") { Load = 1 };
            var gate = new FollowerActuator("dl12.gate", FollowerParams.Dl12Gate());
            var g = Mech.Graph("school", strip, gate);
            Assert.Equal(1.3, gate.Position);                     // reset follows the source
            strip.Load = 0;
            bool slam = false, startle = false;
            Mech.RunUntil(g, () =>
            {
                slam |= Mech.Emitted(g, "dl12.gate", FollowerEvent.Slam);
                startle |= Mech.Emitted(g, "dl12.gate", FollowerEvent.Startle);
                return gate.Position <= 0;
            }, pose: Mech.Pose(209.4 - 1.0));
            Assert.True(slam);
            Assert.False(startle);
            strip.Load = 1;
            Mech.Run(g, 60);
            Assert.Equal(0.5, gate.Position, 9);
            Assert.Equal(0, g.Log.Count);                         // no ticks while rising (state already Rising)
        }

        [Fact]
        public void Follower_RestoredMidFall_ContinuesBitIdentically()
        {
            var (ga, a, pa) = Dl03(1);
            pa.Load = 0;
            Mech.Run(ga, 10);
            var (gb, b, pb) = Dl03(0.3);
            gb.Restore(Mech.Snapshot(ga));
            Assert.Equal(0.0, pb.Load);
            for (int i = 0; i < 40; i++)
            {
                ga.Step(Dt, Mech.Pose(GateX - 1));
                gb.Step(Dt, Mech.Pose(GateX - 1));
                Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
                Assert.Equal(Mech.Events(ga).Count, Mech.Events(gb).Count);
            }
        }

        // ---- CrankActuator --------------------------------------------------------------------------------------------------

        [Fact]
        public void Crank_FiveStrokesOpenIt_OneFifthEach_EasedOver12Frames_L1880_L1889()
        {
            var crank = new CrankActuator("dl01.crank", CrankParams.Dl01Crank());
            var g = Mech.Graph("hall", crank);
            var strokes = new List<int>();
            var at = new Dictionary<int, double>();
            int steps = Mech.PlayAct(g, crank, onStep: (k, f) =>
            {
                foreach (var e in Mech.Events(g)) if (e.Kind == MechanismEventKind.Event && e.Code == (int)CrankEvent.Stroke) strokes.Add(e.Index);
                at[k] = crank.Position;
                if (k == 75) Assert.Equal(60 + 30, crank.WheelDeg, 9);
            });
            Assert.Equal(300, steps);                             // 5 × 24 frames at 0.4 a step
            Assert.Equal(new[] { 1, 2, 3, 4, 5 }, strokes);
            Assert.Equal(Smooth.Step(0.5) / 5, at[15], 9);        // f 6
            Assert.Equal(0.2, at[30], 9);                         // f 12: the stroke's rise is done
            Assert.Equal(0.2, at[60], 9);                         // the wrap step uses the old count (L1886)
            Assert.Equal((1 + Smooth.Step(0.5)) / 5, at[75], 9);  // f 30
            Assert.Equal(CrankState.Done, crank.State);
            Assert.Equal(1.0, crank.Position);
            Assert.Equal(300, crank.WheelDeg);
            Assert.False(crank.IsAvailable(new InteractionQuery(9.62, 0, 0, 1, true, false, HoldKind.None, null, null)));
        }

        [Fact]
        public void Crank_StateIsCrankingWhileTheActRuns_IdleWhenItStops()
        {
            var crank = new CrankActuator("dl10.serviceCrank", new CrankParams { Station = new Station(120.0, 0.36, 1), Strokes = 4, CancelAfter = 0.5 });
            var g = Mech.Graph(crank);
            int steps = Mech.PlayAct(g, crank, move: k => 1.0);
            Assert.Equal(31, steps);                              // moving only stops it after 0.5 s (L4575)
            Assert.Equal(CrankState.Cranking, crank.State);
            Mech.Run(g, 1);
            Assert.True(Mech.Entered(g, "dl10.serviceCrank", CrankState.Idle));
        }

        [Fact]
        public void Crank_Dl10_HoldsWhereLeft_AndANewActCountsAfresh_L4567_L4575()
        {
            var crank = new CrankActuator("dl10.serviceCrank", new CrankParams { Station = new Station(120.0, 0.36, 1), Strokes = 4, CancelAfter = 0.5 });
            var g = Mech.Graph(crank);
            Mech.PlayAct(g, crank, move: k => k > 132 ? 1.0 : 0);   // two strokes and a bit, then walks off
            double held = crank.Position;
            Assert.InRange(held, 0.5, 0.75);
            Mech.Run(g, 30);
            Assert.Equal(held, crank.Position);
            Mech.PlayAct(g, crank, max: 120);                     // a new act: two strokes, (0 + 2) / 4 < held
            Assert.Equal(held, crank.Position);
            Assert.Equal(CrankState.Cranking, crank.State);
        }

        [Theory]
        [InlineData("hall", CrankState.Idle, 0, 0)]
        [InlineData("door", CrankState.Done, 1, 300)]
        public void Crank_ResetFromCheckpoint_L8023_L8024(string cp, CrankState state, double open, double wheel)
        {
            var crank = new CrankActuator("dl01.crank", CrankParams.Dl01Crank());
            Mech.Graph(cp, crank);
            Assert.Equal(state, crank.State);
            Assert.Equal(open, crank.Position);
            Assert.Equal(wheel, crank.WheelDeg);
        }

        // ---- Door -----------------------------------------------------------------------------------------------------------

        [Fact]
        public void Door_FollowsTheCrank_ToDoorHeightMinus5cm_L7957()
        {
            var crank = new TestSource("dl01.crank");
            var door = new Door("dl01.door", DoorParams.Dl01Door());
            var g = Mech.Graph(crank, door);
            crank.Position = 0.5;
            Mech.Run(g, 1);
            Assert.Equal(0.5, door.Position, 12);
            Assert.True(Mech.Entered(g, "dl01.door", DoorState.Opening));
            crank.Position = 1;
            Mech.Run(g, 1);
            Assert.Equal(1.0, door.Position, 12);
            Assert.True(door.Engaged);
        }

        [Fact]
        public void Door_Linear_OpensOverDuration_AdvancingOnTheTriggerStep_L5737()
        {
            var seats = new TestSource("dl15.seats");
            var door = new Door("dl15.classDoor", DoorParams.Dl15ClassDoor());
            var g = Mech.Graph("class6", seats, door);
            Mech.Run(g, 10);
            Assert.Equal(DoorState.Closed, door.State);
            seats.Engaged = true;
            Mech.Run(g, 1);
            Assert.Equal(Dt / 1.6, door.Position, 12);
            int n = Mech.RunUntil(g, () => door.Engaged);
            Assert.Equal(95, n);                                  // 96 steps of 1/60 = 1.6 s
            Assert.Equal(1.0, door.Position);
            seats.Engaged = false;
            Mech.Run(g, 10);
            Assert.True(door.Engaged);                            // never closes
        }

        [Fact]
        public void Door_Delay_IsStrictlyMoreThanTheHold_L5789()
        {
            var latch = new TestSource("dl17.latch");
            var door = new Door("dl17.stairDoor", DoorParams.Dl17StairDoor());
            var g = Mech.Graph("workshop", latch, door);
            g.Flags.Set(StoryFlags.Dl17DrawerRead);               // the drawing read first (L5776)
            latch.Engaged = true;
            int n = Mech.RunUntil(g, () => door.State == DoorState.Opening);
            Assert.InRange(n, 49, 50);                            // clock − latchAt > 0.8
            Assert.Equal(Dt / 1.8, door.Position, 12);
        }

        [Fact]
        public void Door_Dl17_WaitsForTheDrawerRead_ThenOpensAtOnceIfTheLatchHeldLongEnough_L5776_L5789()
        {
            var latch = new TestSource("dl17.latch");
            var door = new Door("dl17.stairDoor", DoorParams.Dl17StairDoor());
            var g = Mech.Graph("workshop", latch, door);
            latch.Engaged = true;
            Mech.Run(g, 300);                                     // latched 5 s, drawing unread: the door waits
            Assert.Equal(DoorState.Closed, door.State);
            g.Reset(Mech.Cp("workshop"));
            Assert.Equal(DoorState.Closed, door.State);           // nor does a reload open it
            Mech.Run(g, 60);
            g.Flags.Set(StoryFlags.Dl17DrawerRead);
            Mech.Run(g, 1);
            Assert.Equal(DoorState.Opening, door.State);          // clock − latchAt > 0.8 long since
            g.Reset(Mech.Cp("workshop"));
            Assert.Equal(DoorState.Open, door.State);             // read and latched: derived open
        }

        [Fact]
        public void Door_ReadBeforeTheLatch_KeepsTheDelay_L5789()
        {
            var latch = new TestSource("dl17.latch");
            var door = new Door("dl17.stairDoor", DoorParams.Dl17StairDoor());
            var g = Mech.Graph("workshop", latch, door);
            g.Flags.Set(StoryFlags.Dl17DrawerRead);
            Mech.Run(g, 30);
            latch.Engaged = true;
            Assert.InRange(Mech.RunUntil(g, () => door.State == DoorState.Opening), 49, 50);
        }

        [Fact]
        public void Door_TriggerDroppingRestartsTheDelay_L6224_L6225()
        {
            var dark = new TestSource("dl14a.nightLight");
            var door = new Door("dl14a.door", DoorParams.Dl14aDoor());
            var g = Mech.Graph("dorm", dark, door);
            dark.Engaged = true;
            Mech.Run(g, 60);
            dark.Engaged = false;
            Mech.Run(g, 1);
            dark.Engaged = true;
            Mech.Run(g, 60);
            Assert.Equal(DoorState.Closed, door.State);           // 1.0 s since it went dark again
            int n = Mech.RunUntil(g, () => door.State != DoorState.Closed);
            Assert.InRange(n, 13, 14);                            // 1.2 s after the second time
        }

        [Fact]
        public void Door_EaseOutCubic_C114_L7276_L7277()
        {
            var cord = new TestSource("dl11.cord");
            var door = new Door("dl11.c114Door", DoorParams.Dl11C114Door("dl11.cord"));
            var g = Mech.Graph("bedroom", cord, door);
            cord.Engaged = true;
            Mech.Run(g, 48);
            Assert.Equal(95 * (1 - 0.125), door.Position, 9);
        }

        private static double ShutterAt(double t, bool calm)
        {
            double k = Math.Min(1, t / 0.9);
            double settle = 1 + 0.9 * Math.Pow(k - 1, 3) + 1.5 * Math.Pow(k - 1, 2) * (k < 1 ? 1 : 0);
            double jitter = t < 0.8 && !calm ? Math.Sin(t * 90) * 0.4 * (1 - t / 0.8) : 0;
            return 15 * Math.Min(1.04, settle) + jitter;
        }

        [Theory]
        [InlineData(false)]
        [InlineData(true)]
        public void Door_ShutterSwing_SnapsTo104Percent_SettlesTo15By0_9s_L1691_L1696(bool calm)
        {
            var latch = new TestSource("dl01.latch");
            var shutter = new Door("dl01.shutter", DoorParams.Dl01Shutter());
            var g = Mech.Graph(latch, shutter);
            g.Calm = calm;
            latch.Engaged = true;
            int cues = 0;
            for (int n = 1; n <= 60; n++)
            {
                Mech.Run(g, 1);
                double t = (n - 1) * Dt;                          // t = clock − releaseTime: 0 on the release step
                Assert.Equal(Math.Min(t, 0.9), shutter.Elapsed, 12);   // stops once open
                Assert.Equal(ShutterAt(t, calm), shutter.Position, 9);
                if (Mech.Emitted(g, "dl01.shutter", DoorEvent.Cue)) { cues++; Assert.InRange(t, 0.56, 0.56 + Dt); }
                if (n == 1) Assert.Equal(15.6, shutter.Position, 12);
            }
            Assert.Equal(1, cues);
            Assert.Equal(15.0, shutter.Position);
            Assert.Equal(DoorState.Open, shutter.State);
        }

        [Theory]
        [InlineData(0, 1.56)] [InlineData(0.3, 1.56 - 0.5 * 9.8 * 0.09 * 1.8)] [InlineData(0.54, 0.12)] [InlineData(0.62, 0.15)] [InlineData(5, 0.12)]
        public void Door_ShutterCounterweight_Falls0_54sThenBounces_L1697_L1699(double t, double y)
        {
            Assert.Equal(y, Door.ShutterCounterweightY(t), 9);
        }

        [Theory]
        [InlineData(false, DoorState.Closed, 0)]
        [InlineData(true, DoorState.Open, 15)]
        public void Door_ResetIsDerivedFromItsTrigger_L8022(bool released, DoorState state, double pos)
        {
            var latch = new TestSource("dl01.latch") { Engaged = released };
            var shutter = new Door("dl01.shutter", DoorParams.Dl01Shutter());
            var g = Mech.Graph(latch, shutter);
            Assert.Equal(state, shutter.State);
            Assert.Equal(pos, shutter.Position);
            Assert.Equal(released ? 0.12 : 1.56, Door.ShutterCounterweightY(shutter.Elapsed), 12);
            Mech.Run(g, 5);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Door_NeedsExactlyOneOfFollowOrTrigger()
        {
            var g = new MechanismGraph();
            g.Add(new Door("t.door", new DoorParams()));
            Assert.Throws<InvalidOperationException>(() => g.Build());
        }
    
        // ---- DL-07: the gallery gate and its bucket (L3892–L3893, L4825–L4837, L4991–L5003) -------------------------------

        private static (MechanismGraph g, GateBucket bucket, BucketGate gate) Dl07(string cp = "landing")
        {
            var bucket = new GateBucket("dl07.bucket", GateBucketParams.Dl07Bucket());
            var gate = new BucketGate("dl07.gate", BucketGateParams.Dl07Gate());
            return (Mech.Graph(cp, bucket, gate), bucket, gate);
        }

        private static int Count(MechanismGraph g, MechanismId id, BucketGateEvent e)
            => Mech.Events(g).FindAll(ev => ev.Id == id && ev.Kind == MechanismEventKind.Event && ev.Code == (int)e).Count;

        [Fact]
        public void BucketGate_NoWeights_StaysShut_AndBlocks()
        {
            var (g, bucket, gate) = Dl07();
            Mech.Run(g, 300);
            Assert.Equal(0, bucket.Weights);
            Assert.Equal(0, gate.Position);
            Assert.Equal(BucketGateState.Shut, gate.State);
            Assert.True(gate.Blocks);
            Assert.False(gate.Engaged);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void BucketGate_OneWeight_TumblesInFor0_7s_RisesTo0_38_AndStallsWithAStrain_L4831_L4959()
        {
            var (g, bucket, gate) = Dl07();
            bucket.Drop();
            Mech.Run(g, 1);
            Assert.True(Mech.Emitted(g, "dl07.bucket", GateBucketEvent.Tumbling));
            Assert.Equal(1, bucket.Tumbling);
            int land = Mech.RunUntil(g, () => Mech.Emitted(g, "dl07.bucket", GateBucketEvent.Landed), 100);
            Assert.Equal(41, land);                                     // 42 steps of 1/60 s = 0.7 s
            Assert.Equal(1, bucket.Weights);
            Assert.Equal(1.0, bucket.Load);
            int strainAt = -1, strains = 0;
            for (int i = 1; i <= 200; i++)
            {
                Mech.Run(g, 1);
                if (Mech.Emitted(g, "dl07.gate", BucketGateEvent.Strain)) { strains++; if (strainAt < 0) strainAt = i; }
            }
            Assert.InRange(strainAt, 50, 52);                           // 0.38 m at 0.45 m/s ≈ 0.84 s
            Assert.Equal(1, strains);                                   // once, when it stalls
            Assert.Equal(0.38, gate.Position, 12);
            Assert.Equal(BucketGateState.Stalled, gate.State);
            Assert.True(gate.Position < 0.58);                          // never a crouch gap (L4826)
            Assert.True(gate.Blocks);
        }

        [Fact]
        public void BucketGate_TwoWeights_RiseTo1_4_At0_45PerSecond_AndOpen_L3892()
        {
            var (g, bucket, gate) = Dl07();
            bucket.Drop();
            Mech.Run(g, 11);                                            // the second follows 0.18 s later (L4992)
            bucket.Drop();
            int strains = 0;
            Mech.RunUntil(g, () => { strains += Count(g, "dl07.gate", BucketGateEvent.Strain); return bucket.Weights == 2; }, 100);
            int open = Mech.RunUntil(g, () => { strains += Count(g, "dl07.gate", BucketGateEvent.Strain); return gate.Engaged; }, 400);
            Assert.Equal(0, strains);                                   // the second lands before the first stalls
            Assert.InRange(open * Dt, 1.4 / 0.45 - 0.35, 1.4 / 0.45);    // most of the rise happens after the second lands
            Assert.Equal(1.4, gate.Position, 12);
            Assert.Equal(BucketGateState.Open, gate.State);
            Assert.True(Mech.Emitted(g, "dl07.gate", BucketGateEvent.Opened));
            Assert.False(gate.Blocks);
            Mech.Run(g, 60);
            Assert.Equal(1.4, gate.Position, 12);
        }

        [Fact]
        public void BucketGate_Transitions_Shut_Rising_Stalled_Rising_Open()
        {
            var (g, bucket, gate) = Dl07();
            var seen = new List<BucketGateState> { gate.State };
            void Watch(int steps)
            {
                for (int i = 0; i < steps; i++)
                {
                    Mech.Run(g, 1);
                    foreach (var e in Mech.Events(g))
                        if (e.Id == "dl07.gate" && e.Kind == MechanismEventKind.State) seen.Add((BucketGateState)e.Code);
                }
            }
            bucket.Drop();
            Watch(200);
            Assert.Equal(BucketGateState.Stalled, gate.State);
            bucket.Drop();
            Watch(400);
            Assert.Equal(new[] { BucketGateState.Shut, BucketGateState.Rising, BucketGateState.Stalled, BucketGateState.Rising, BucketGateState.Open }, seen);
            Assert.Equal(2, bucket.Weights);
        }

        [Fact]
        public void BucketGate_NeverACrouchGap_APartialOpeningAtCrouchHeightIsRefused()
        {
            Assert.Throws<ArgumentException>(() => new BucketGate("t.gate", new BucketGateParams { Bucket = "t.b", PerWeight = 0.55 }));
            Assert.Throws<ArgumentException>(() => new BucketGate("t.gate", new BucketGateParams { Bucket = "t.b", WeightsToOpen = 3 }));   // 0.76 with 2
            var gate = new BucketGate("t.gate", BucketGateParams.Dl07Gate());
            Assert.Equal(0, gate.TargetFor(0));
            Assert.Equal(0.38, gate.TargetFor(1), 12);
            Assert.Equal(1.4, gate.TargetFor(2));
            Assert.Equal(1.4, gate.TargetFor(3));
        }

        [Fact]
        public void BucketGate_SnapshotMidTumbleAndMidRise_ContinuesBitIdentically()
        {
            var (ga, ba, _) = Dl07();
            ba.Drop();
            Mech.Run(ga, 50);                                           // landed, rising
            ba.Drop();
            Mech.Run(ga, 5);                                            // the second in the air
            Assert.Equal(1, ba.Tumbling);
            var (gb, bb, gtb) = Dl07();
            gb.Restore(Mech.Snapshot(ga));
            Assert.Equal(1, bb.Tumbling);
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            for (int i = 0; i < 300; i++)
            {
                ga.Step(Dt, PlayerPose.Away);
                gb.Step(Dt, PlayerPose.Away);
                Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
                Assert.Equal(Mech.Events(ga).Count, Mech.Events(gb).Count);
            }
            Assert.Equal(BucketGateState.Open, gtb.State);
        }

        [Fact]
        public void BucketGate_ASnapshotWithTooManyTumblingWeights_IsRefused()
        {
            var (ga, _, _) = Dl07();
            var s = Mech.Snapshot(ga);
            s.WriteLong("dl07.bucket/n", GateBucket.MaxTumbling + 1);
            var (gb, _, _) = Dl07();
            Assert.Throws<InvalidOperationException>(() => gb.Restore(s));
        }

        [Theory]
        [InlineData("landing", 0, 0.0, BucketGateState.Shut)]
        [InlineData("gallery", 2, 1.4, BucketGateState.Open)]
        [InlineData("goods", 2, 1.4, BucketGateState.Open)]
        public void BucketGate_ResetFromCheckpoint_L4099(string cp, int weights, double y, BucketGateState state)
        {
            var (g, bucket, gate) = Dl07(cp);
            Assert.Equal(weights, bucket.Weights);
            Assert.Equal(0, bucket.Tumbling);
            Assert.Equal(y, gate.Position);
            Assert.Equal(state, gate.State);
            Mech.Run(g, 60);
            Assert.Equal(y, gate.Position);
            Assert.Equal(0, Count(g, "dl07.gate", BucketGateEvent.Strain));
        }

        // ---- DL-10: the service door (L3459, L4565–L4577, L4654) --------------------------------------------------------------

        private static (MechanismGraph g, CrankActuator crank, Door door) Dl10()
        {
            var crank = new CrankActuator("dl10.serviceCrank", CrankParams.Dl10ServiceCrank());
            var door = new Door("dl10.serviceDoor", DoorParams.Dl10ServiceDoor());
            return (Mech.Graph("uponly", crank, door), crank, door);
        }

        [Fact]
        public void ServiceDoor_FourStrokesLiftIt1_45m_L4567_L4570()
        {
            var (g, crank, door) = Dl10();
            Assert.Equal(54 + 72.45, crank.StandX, 12);                 // UO.crankStand
            Assert.Equal(1, crank.Face);
            var strokes = new List<double>();
            int steps = Mech.PlayAct(g, crank, onStep: (k, f) => { if (Mech.Emitted(g, "dl10.serviceCrank", CrankEvent.Stroke)) strokes.Add(door.Position); });
            Assert.Equal(240, steps);                                   // 4 × 24 frames at 0.4 frames a step
            Assert.Equal(4, strokes.Count);
            Assert.Equal(CrankState.Done, crank.State);
            Assert.Equal(1.45, door.Position, 12);
            Assert.Equal(DoorState.Open, door.State);
            Assert.False(crank.IsAvailable(new InteractionQuery(54 + 72.45, 0, 0, 1, true, false, HoldKind.None, null, null)));
        }

        [Fact]
        public void ServiceDoor_ACancelMidWayHoldsItWhereLeft_AndTheNextActResumes_L4318_L4575()
        {
            var (g, crank, door) = Dl10();
            int first = Mech.PlayAct(g, crank, move: k => k > 132 ? 1.0 : 0);   // two strokes and a bit, then walks off
            Assert.Equal(133, first);
            double held = door.Position;
            Assert.InRange(held, 1.45 * 0.5, 1.45 * 0.75);
            Assert.Equal(DoorState.Opening, door.State);
            Mech.Run(g, 120);
            Assert.Equal(held, door.Position);                          // holds where left
            Assert.True(crank.IsAvailable(new InteractionQuery(54 + 72.45, 0, 0, 1, true, false, HoldKind.None, null, null)));
            int resumed = (int)Math.Floor(held / 1.45 * 4 + 0.5);      // Math.round(uo.door · UO.strokes)
            int second = Mech.PlayAct(g, crank);
            Assert.Equal((4 - resumed) * 60, second);                   // only the strokes left
            Assert.Equal(1.45, door.Position, 12);
            Assert.Equal(CrankState.Done, crank.State);
        }

        [Fact]
        public void ServiceDoor_SnapshotMidAct_ContinuesBitIdentically()
        {
            var (ga, ca, _) = Dl10();
            Mech.PlayAct(ga, ca, max: 100);
            var (gb, cb, db) = Dl10();
            gb.Restore(Mech.Snapshot(ga));
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            int a = Mech.PlayAct(ga, ca, startStep: 101), b = Mech.PlayAct(gb, cb, startStep: 101);
            Assert.Equal(a, b);
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            Assert.Equal(1.45, db.Position, 12);
        }
}
}
