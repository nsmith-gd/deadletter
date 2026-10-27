using System;
using System.Collections.Generic;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>A settable loose thing for plates: x, where it rests, and its carrier's x.</summary>
    internal sealed class TestBody : Mechanism, IPlateBody
    {
        public TestBody(MechanismId id, double x = 0, BodySupport support = BodySupport.Floor) : base(id) { X = x; Support = support; }
        public double X { get; set; }
        public double CarrierX { get; set; } = double.NaN;
        public double SupportX => double.IsNaN(CarrierX) ? X : CarrierX;
        public BodySupport Support { get; set; }
        public override void Reset(in Checkpoint cp) { }
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("cx", CarrierX); w.WriteLong("s", (long)Support);
        }
        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); CarrierX = r.ReadDouble("cx"); Support = (BodySupport)r.ReadLong("s");
        }
    }

    internal static class PlateKit
    {
        /// <summary>Runs <paramref name="a"/> on, snapshots, restores into <paramref name="b"/>, and compares both every step.</summary>
        public static void RoundTrip(MechanismGraph a, MechanismGraph b, int steps, Func<int, PlayerPose> pose = null)
        {
            b.Restore(Mech.Snapshot(a));
            Assert.Equal(Mech.Dump(a), Mech.Dump(b));
            for (int k = 0; k < steps; k++)
            {
                var p = pose?.Invoke(k) ?? PlayerPose.Away;
                a.Step(Mech.Dt, p);
                b.Step(Mech.Dt, p);
                Assert.Equal(Mech.Dump(a), Mech.Dump(b));
                Assert.Equal(Mech.Events(a).Count, Mech.Events(b).Count);
            }
        }

        public static int Count(MechanismGraph g, MechanismId id, int code)
        {
            int n = 0;
            foreach (var e in Mech.Events(g)) if (e.Id == id && e.Kind == MechanismEventKind.Event && e.Code == code) n++;
            return n;
        }

        public static MechanismEvent? Find(MechanismGraph g, MechanismId id, int code)
        {
            foreach (var e in Mech.Events(g)) if (e.Id == id && e.Kind == MechanismEventKind.Event && e.Code == code) return e;
            return null;
        }
    }

    /// <summary>Load plates, scales, strips and seats (§4.13a).</summary>
    public class PlateTests
    {
        private static PlayerPose On(double x, double y = 0) => Mech.Pose(x, y);

        // ---- LoadPlate: DL-01 curio scale ----------------------------------------------------------------------------------

        [Theory]
        [InlineData(1.45, 0.0, 1)] [InlineData(1.24, 0.0, 1)] [InlineData(1.66, 0.0, 1)] [InlineData(1.67, 0.0, 0)] [InlineData(1.23, 0.0, 0)]
        [InlineData(1.45, 0.099, 1)] [InlineData(1.45, 0.1, 0)]
        public void Scale_FeelsHimWithin022OfX145BelowY01_L4767(double x, double y, double load)
        {
            var s = new LoadPlate("dl01.scale", LoadPlateParams.Dl01Scale());
            var g = Mech.Graph(s);
            g.Step(Mech.Dt, On(x, y));
            Assert.Equal(load, s.Load);
        }

        [Fact]
        public void Scale_NeedleEasesAtDt3_L4768()
        {
            var s = new LoadPlate("dl01.scale", LoadPlateParams.Dl01Scale());
            var g = Mech.Graph(s);
            double needle = 0;
            for (int i = 0; i < 90; i++)
            {
                g.Step(Mech.Dt, On(1.45));
                needle += (1 - needle) * Math.Min(1, Mech.Dt * 3);
                Assert.Equal(needle, s.Needle, 12);
            }
            for (int i = 0; i < 30; i++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                needle += (0 - needle) * Math.Min(1, Mech.Dt * 3);
                Assert.Equal(needle, s.Needle, 12);
            }
            Assert.Equal(LoadPlateState.Empty, s.State);
        }

        // ---- LoadPlate: DL-03 ----------------------------------------------------------------------------------------------

        private static (MechanismGraph g, LoadPlate plate, TestBody trolley, TestBody weight) Dl03(string cp = "weighroom")
        {
            var trolley = new TestBody("dl03.trolley", 27.55);
            var weight = new TestBody("dl03.weight", 25.62);
            var plate = new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate());
            return (Mech.Graph(cp, trolley, weight, plate), plate, trolley, weight);
        }

        [Theory]
        // him x, him y, trolley x, weight support, weight x / carrier, load
        [InlineData(29.2, 0.0, 27.55, BodySupport.Floor, 25.62, 1.0)]
        [InlineData(28.79, 0.0, 27.55, BodySupport.Floor, 25.62, 1.0)]       // the plate ± 0.02
        [InlineData(28.78, 0.0, 27.55, BodySupport.Floor, 25.62, 0.0)]
        [InlineData(29.2, 0.24, 27.55, BodySupport.Floor, 25.62, 1.0)]
        [InlineData(29.2, 0.25, 27.55, BodySupport.Floor, 25.62, 0.0)]
        [InlineData(20.0, 0.0, 29.2, BodySupport.Floor, 25.62, 0.3)]          // trolley alone
        [InlineData(20.0, 0.0, 29.56, BodySupport.Floor, 25.62, 0.3)]
        [InlineData(20.0, 0.0, 29.58, BodySupport.Floor, 25.62, 0.0)]
        [InlineData(20.0, 0.0, 27.55, BodySupport.Floor, 29.0, 0.42)]         // weight on the floor on the plate
        [InlineData(20.0, 0.0, 29.0, BodySupport.Carrier, 29.0, 0.72)]        // weight on the trolley, both on the plate
        [InlineData(20.0, 0.0, 27.55, BodySupport.Carrier, 27.55, 0.0)]       // ... trolley off the plate
        [InlineData(29.2, 0.0, 27.55, BodySupport.Carried, 29.2, 1.42)]       // carried by him on the plate
        [InlineData(20.0, 0.0, 27.55, BodySupport.Carried, 29.2, 0.0)]        // carried, he is off
        [InlineData(29.2, 0.0, 29.2, BodySupport.Carrier, 29.2, 1.72)]
        public void Dl03_LoadIsHim1_Trolley03_Weight042_L2229_L2238(double hx, double hy, double tx, BodySupport ws, double wx, double load)
        {
            var (g, plate, trolley, weight) = Dl03();
            trolley.X = tx;
            weight.Support = ws;
            if (ws == BodySupport.Carrier) { weight.X = tx - 0.12; weight.CarrierX = tx; } else weight.X = wx;
            g.Step(Mech.Dt, On(hx, hy));
            Assert.Equal(load, plate.Load, 12);
        }

        [Fact]
        public void Dl03_PressOnceAt005_NeedleAtDt5_L2373_L2374()
        {
            var (g, plate, trolley, _) = Dl03();
            Mech.Run(g, 3);
            Assert.False(Mech.Emitted(g, "dl03.plate", LoadPlateEvent.Press));
            trolley.X = 29.2;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Emitted(g, "dl03.plate", LoadPlateEvent.Press));
            Assert.True(Mech.Entered(g, "dl03.plate", LoadPlateState.Loaded));
            Assert.Equal(0.3 * 5 / 60.0, plate.Needle, 12);
            g.Step(Mech.Dt, On(29.2));                        // 1.3: needle aims at min(1, load)
            Assert.False(Mech.Emitted(g, "dl03.plate", LoadPlateEvent.Press));
            double n1 = 0.3 * 5 / 60.0;
            Assert.Equal(n1 + (1 - n1) * 5 / 60.0, plate.Needle, 12);
        }

        [Fact]
        public void Dl03_PassesWith068WithoutHim_AndTheGateAtThatHeight_L2396()
        {
            var (g, plate, trolley, weight) = Dl03();
            trolley.X = 29.2;
            g.Step(Mech.Dt, On(29.2));
            Assert.Equal(1.3, plate.Load, 12);
            Assert.Equal(0.3, plate.LoadWithoutPlayer, 12);
            Assert.False(plate.Passing);
            weight.Support = BodySupport.Carrier; weight.CarrierX = 29.2;
            g.Step(Mech.Dt, On(29.2));
            Assert.Equal(0.72, plate.LoadWithoutPlayer, 12);
            Assert.True(plate.Passing);
            Assert.False(plate.SolvedWith(0.68 * 1.2 - 0.0101, 1.2));
            Assert.True(plate.SolvedWith(0.68 * 1.2 - 0.0099, 1.2));
            weight.Support = BodySupport.Carried;               // in his claws: it only counts with him
            g.Step(Mech.Dt, On(29.2));
            Assert.Equal(1.72, plate.Load, 12);
            Assert.False(plate.Passing);
        }

        [Fact]
        public void Dl03_GateFollowsThePlate_RisesAt055_L2378_L2380()
        {
            var trolley = new TestBody("dl03.trolley", 29.2);
            var weight = new TestBody("dl03.weight", 25.62);
            var plate = new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate());
            var gate = new FollowerActuator("dl03.gate", FollowerParams.Dl03Gate());
            var g = Mech.Graph("weighroom", trolley, weight, plate, gate);
            Assert.Equal(0.3 * 1.2, gate.Position, 12);          // reset derives from the plate (L8030)
            weight.Support = BodySupport.Carrier; weight.CarrierX = 29.2;
            int n = Mech.RunUntil(g, () => gate.Position >= 0.72 * 1.2 - 1e-12);
            Assert.InRange(n, 55, 56);                            // 0.504 m at 0.55 m/s
        }

        [Theory]
        [InlineData("weighroom", 0.0)]
        [InlineData("solved", 0.72)]
        public void Dl03_ResetDerivesFromTheBodies_L8025_L8028(string cp, double load)
        {
            bool solved = cp == "solved";
            var trolley = new TestBody("dl03.trolley", solved ? (28.8 + 29.55) / 2 : 27.55);
            var weight = new TestBody("dl03.weight", solved ? 29.0 : 25.62, solved ? BodySupport.Carrier : BodySupport.Floor) { CarrierX = solved ? (28.8 + 29.55) / 2 : double.NaN };
            var plate = new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate());
            var g = Mech.Graph(cp, trolley, weight, plate);
            Assert.Equal(load, plate.Load, 12);
            Assert.Equal(load, plate.Needle, 12);
            Assert.Equal(solved, plate.Engaged);
            Assert.Equal(solved, plate.Passing);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Dl03_RestoredMidEase_ContinuesIdentically()
        {
            var (a, _, ta, _) = Dl03();
            ta.X = 29.2;
            Mech.Run(a, 10, On(29.0));
            var (b, _, _, _) = Dl03("start");
            PlateKit.RoundTrip(a, b, 60, k => k < 30 ? On(29.0) : PlayerPose.Away);
        }

        // ---- LoadPlate: DL-08 pan ------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(83.24, 20.0, 1.6, 0.0)]
        [InlineData(83.50, 20.0, 1.6, 1.05 * 0.26 / 0.52)]
        [InlineData(83.76, 20.0, 1.6, 1.05)]
        [InlineData(84.40, 20.0, 1.6, 1.05)]
        [InlineData(83.24, 84.0, 1.6, 0.5)]
        [InlineData(83.24, 83.47, 1.6, 0.5)]
        [InlineData(83.24, 83.46, 1.6, 0.0)]
        [InlineData(83.24, 84.93, 2.19, 0.5)]
        [InlineData(83.24, 84.0, 2.2, 0.0)]
        [InlineData(84.40, 84.0, 1.6, 1.55)]
        public void Dl08Pan_TrolleyRollsOnGradually_PlusHalfForHim_L3022_L3030(double tx, double hx, double hy, double load)
        {
            var trolley = new TestBody("dl08.trolley", tx);
            var pan = new LoadPlate("dl08.pan", LoadPlateParams.Dl08Pan());
            var g = Mech.Graph("goods", trolley, pan);
            g.Step(Mech.Dt, On(hx, hy));
            Assert.Equal(load, pan.Load, 9);
        }

        // ---- LoadPlate: DL-09 tray -----------------------------------------------------------------------------------------

        [Fact]
        public void Dl09Tray_CountsPlates_GaugeReadsHalfAPlateEach_L5016_L5054()
        {
            var p0 = new TestBody("dl09.plate0", 100);
            var p1 = new TestBody("dl09.plate1", 101);
            var tray = new LoadPlate("dl09.tray", LoadPlateParams.Dl09Tray());
            var g = Mech.Graph("tunnel", p0, p1, tray);
            Assert.Equal(0, tray.Load);
            p0.Support = BodySupport.Placed;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(1, tray.Load);
            Assert.False(tray.Engaged);
            Assert.Equal(0.5 * 3 / 60.0, tray.Needle, 12);
            Mech.Run(g, 600);
            Assert.Equal(0.5, tray.Needle, 6);
            p1.Support = BodySupport.Placed;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl09.tray", LoadPlateState.Loaded));
            Assert.Equal(2, tray.Load);
            p1.Support = BodySupport.Carried;                  // lifted out again
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl09.tray", LoadPlateState.Empty));
        }

        // ---- LoadPlate: DL-10 car plate and gate ---------------------------------------------------------------------------

        private static (MechanismGraph g, TestBody suitcase, LoadPlate plate, Door gate) Dl10(string cp)
        {
            bool loaded = Checkpoint.Prototype(cp).Past("ringc");
            var suitcase = new TestBody("dl10.case", 121.3, loaded ? BodySupport.Placed : BodySupport.Floor);
            var plate = new LoadPlate("dl10.carPlate", LoadPlateParams.Dl10CarPlate());
            var gate = new Door("dl10.carGate", PlateOutputs.Dl10CarGate());
            return (Mech.Graph(cp, suitcase, plate, gate), suitcase, plate, gate);
        }

        [Fact]
        public void Dl10_GateShuts08sAfterLoading_Over14s_LampsAt025Plus03i_L4623_L4647()
        {
            var (g, suitcase, plate, gate) = Dl10("uponly");
            Mech.Run(g, 5);
            suitcase.Support = BodySupport.Placed;               // set down at SetDown f14 (L4558)
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(0, plate.EngagedFor);
            int start = Mech.RunUntil(g, () => gate.State == DoorState.Opening) + 1;
            Assert.Equal(49, start);                               // clock − loadedAt > 0.8
            Assert.Equal(1 / 60.0 / 1.4, gate.Position, 12);       // gate += dt / 1.4 on that step
            int shut = Mech.RunUntil(g, () => gate.State == DoorState.Open);
            Assert.InRange(shut, 83, 84);
            Assert.True(plate.SillLampLit(0) && plate.SillLampLit(1) && plate.SillLampLit(2));
        }

        [Fact]
        public void Dl10_SillLampsLightOneByOne_L4647()
        {
            var (g, suitcase, plate, _) = Dl10("uponly");
            suitcase.Support = BodySupport.Placed;
            g.Step(Mech.Dt, PlayerPose.Away);
            var first = new int[3];
            for (int k = 1; k <= 120; k++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                for (int i = 0; i < 3; i++) if (first[i] == 0 && plate.SillLampLit(i)) first[i] = k;
            }
            Assert.InRange(first[0], 15, 16);
            Assert.InRange(first[1], 33, 34);
            Assert.InRange(first[2], 51, 52);
        }

        [Fact]
        public void Dl10_NeedleAtDt25_GaugeAtDt15_L4641_L4645()
        {
            var (g, suitcase, plate, _) = Dl10("uponly");
            suitcase.Support = BodySupport.Placed;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(2.5 / 60, plate.Needle, 12);
            Assert.Equal(1.5 / 60, plate.Gauge, 12);
        }

        [Theory]
        [InlineData("uponly", false, 0.0)]
        [InlineData("ringc", true, 1.0)]
        public void Dl10_ResetFromCheckpoint_L4101(string cp, bool loaded, double gateK)
        {
            var (g, _, plate, gate) = Dl10(cp);
            Assert.Equal(loaded, plate.Engaged);
            Assert.Equal(gateK, gate.Position);
            Assert.Equal(loaded, plate.SillLampLit(2));
            Assert.Equal(gateK, plate.Needle);
            Assert.Equal(0, g.Log.Count);
        }

        // ---- LoadPlate: DL-16a ---------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(false, false, 0)]
        [InlineData(true, false, 1)]
        [InlineData(true, true, 1)]
        public void Dl16a_CarLoadJudgedAgainstNeed0_L6171_L6174(bool tin1, bool tin2, int verdict)
        {
            var t1 = new TestBody("dl16a.tin1", 312.85, tin1 ? BodySupport.Placed : BodySupport.Floor);
            var t2 = new TestBody("dl16a.tin2", 313.15, tin2 ? BodySupport.Placed : BodySupport.Floor);
            var car = new LoadPlate("dl16a.carLoad", LoadPlateParams.Dl16aCarLoad());
            var g = Mech.Graph("kitchen", t1, t2, car);
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal((tin1 ? 1 : 0) + (tin2 ? 1 : 0), car.Load);
            Assert.Equal(verdict, car.Judge(LoadPlateParams.Dl16aNeed));
            Assert.Equal(-1, car.Judge(2.5));
        }

        // ---- WeighScale: DL-05 ---------------------------------------------------------------------------------------------

        private const double BodyPlate = 13 + 41.80, Body0 = 13 + 39.30, Drum0 = 13 + 40.45, DrumPark = 13 + 43.02;

        private static (MechanismGraph g, TestBody body, TestBody drum, WeighScale scale, Door hatch, Door flag) Dl05(string cp = "ration")
        {
            bool done = Checkpoint.Prototype(cp).Past("hatch");
            var drum = new TestBody("dl05.drum", done ? DrumPark : Drum0);
            var body = new TestBody("dl05.body", done ? BodyPlate : Body0);
            var scale = new WeighScale("dl05.weighIn", WeighScaleParams.Dl05WeighIn());
            var hatch = new Door("dl05.hatch", PlateOutputs.Dl05Hatch());
            var flag = new Door("dl05.servedFlag", PlateOutputs.Dl05ServedFlag());
            return (Mech.Graph(cp, drum, body, scale, hatch, flag), body, drum, scale, hatch, flag);
        }

        [Theory]
        [InlineData(0, 0, false, WeighReading.Empty)]
        [InlineData(0, 0, true, WeighReading.Under)]                  // he alone: 0.2
        [InlineData(BodyPlate, 0, false, WeighReading.Person)]        // the body: 1
        [InlineData(BodyPlate, 0, true, WeighReading.Over)]           // 1.2 > 1.15
        [InlineData(0, BodyPlate, false, WeighReading.Over)]          // the drum: 1.7
        [InlineData(BodyPlate - 0.83, 0, false, WeighReading.Under)]  // the body half on (0.42)
        [InlineData(BodyPlate - 0.083, 0, false, WeighReading.Person)]
        public void WeighIn_Bands_Empty_Under_Person_Over_L4889_L4891(double bodyX, double drumX, bool him, WeighReading reading)
        {
            var (g, body, drum, scale, _, _) = Dl05();
            body.X = bodyX == 0 ? Body0 : bodyX;
            drum.X = drumX == 0 ? Drum0 : drumX;
            g.Step(Mech.Dt, him ? On(54.2) : PlayerPose.Away);
            Assert.Equal(reading, scale.Reading);
        }

        [Theory]
        [InlineData(53.60, 0.0)] [InlineData(53.85 - 0.225, 0.0)] [InlineData(53.85, 0.5)] [InlineData(53.85 + 0.225, 1.0)]
        public void WeighIn_DrumShareIsItsWidthOnThePlate_L4889(double drumX, double share)
        {
            var (g, _, drum, scale, _, _) = Dl05();
            drum.X = drumX;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(1.7 * share, scale.Load, 9);
        }

        [Fact]
        public void WeighIn_ReadingEvents_WithTheirSoundDelays_L4892_L4898()
        {
            var (g, body, drum, scale, _, _) = Dl05();
            g.Step(Mech.Dt, On(54.2));
            var e = PlateKit.Find(g, "dl05.weighIn", (int)WeighEvent.Reading).Value;
            Assert.Equal((int)WeighReading.Under, e.Index);
            Assert.Equal(0.35, e.Value);
            drum.X = BodyPlate;
            g.Step(Mech.Dt, PlayerPose.Away);
            e = PlateKit.Find(g, "dl05.weighIn", (int)WeighEvent.Reading).Value;
            Assert.Equal((int)WeighReading.Over, e.Index);
            Assert.Equal(0.3, e.Value);
            drum.X = Drum0; body.X = BodyPlate;
            g.Step(Mech.Dt, PlayerPose.Away);
            e = PlateKit.Find(g, "dl05.weighIn", (int)WeighEvent.Reading).Value;
            Assert.Equal((int)WeighReading.Person, e.Index);
            Assert.Equal(0, e.Value);
        }

        [Fact]
        public void WeighIn_PersonHeldOneSecond_Serves_ThenLatches_L4899()
        {
            var (g, body, _, scale, hatch, flag) = Dl05();
            body.X = BodyPlate;
            g.Step(Mech.Dt, PlayerPose.Away);
            int n = Mech.RunUntil(g, () => scale.Engaged);
            Assert.InRange(n, 60, 61);                               // clock − since > 1.0
            Assert.True(Mech.Emitted(g, "dl05.weighIn", WeighEvent.Served));
            Assert.True(Mech.Entered(g, "dl05.hatch", DoorState.Opening));   // same step
            Assert.Equal(0.22 / 60, hatch.Position, 12);
            Assert.Equal(1 / 60.0 / 0.5, flag.Position, 12);
            body.X = Body0;                                          // dragged off again: still served
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(WeighReading.Person, scale.Reading);
            Assert.True(scale.Engaged);
            int open = Mech.RunUntil(g, () => hatch.Engaged);
            Assert.InRange(open, 172, 174);                          // 0.64 m at 0.22 m/s
            Assert.Equal(0.64, hatch.Position);
            Assert.Equal(1, flag.Position);
        }

        [Fact]
        public void WeighIn_PersonBroken_DoesNotServe_L4892()
        {
            var (g, body, _, scale, _, _) = Dl05();
            body.X = BodyPlate;
            Mech.Run(g, 50);
            body.X = Body0;
            Mech.Run(g, 5);
            body.X = BodyPlate;
            Mech.Run(g, 55);
            Assert.False(scale.Engaged);
            Mech.Run(g, 10);
            Assert.True(scale.Engaged);
        }

        [Fact]
        public void WeighIn_NeedleIsADampedSpringToPersonTimesW_L4901_L4903()
        {
            var (g, body, _, scale, _, _) = Dl05();
            body.X = BodyPlate;
            double needle = 0, nv = 0, dt = Mech.Dt;
            int ticks = 0, expectTicks = 0;
            for (int i = 0; i < 50; i++)
            {
                g.Step(dt, PlayerPose.Away);
                double was = needle;
                nv += ((-140 * 1 - needle) * 30 - nv * 7) * dt; needle += nv * dt;
                if (Math.Floor(was / 20) != Math.Floor(needle / 20)) expectTicks++;
                ticks += PlateKit.Count(g, "dl05.weighIn", (int)WeighEvent.Tick);
                Assert.Equal(needle, scale.Needle, 9);
            }
            Assert.True(expectTicks >= 7);
            Assert.Equal(expectTicks, ticks);
        }

        [Fact]
        public void WeighIn_DrumSwingsThroughPerson_TwitchesTheHatch_WithCooldown_L4908_L4920()
        {
            var (g, _, drum, scale, _, _) = Dl05();
            drum.X = BodyPlate;
            int twitch = -1;
            double maxLift = 0;
            for (int k = 1; k <= 60; k++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                if (twitch < 0 && Mech.Emitted(g, "dl05.weighIn", WeighEvent.Twitch)) twitch = k;
                maxLift = Math.Max(maxLift, scale.TwitchOffset);
            }
            Assert.True(twitch > 0);
            Assert.InRange(maxLift, 0.13, 0.14);
            Assert.False(scale.Engaged);                           // the drum reads OVER
            Assert.Equal(WeighReading.Over, scale.Reading);
        }

        [Fact]
        public void WeighIn_DipEasesAtDt8_L4913()
        {
            var (g, body, _, scale, _, _) = Dl05();
            body.X = BodyPlate;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(8 / 60.0, scale.Dip, 12);
        }

        [Theory]
        [InlineData("ration", false)]
        [InlineData("hatch", true)]
        [InlineData("bay", false)]
        public void WeighIn_ResetFromCheckpoint_L4097_L4098(string cp, bool served)
        {
            var (g, _, _, scale, hatch, flag) = Dl05(cp);
            Assert.Equal(served, scale.Engaged);
            Assert.Equal(served ? WeighReading.Person : WeighReading.Empty, scale.Reading);
            Assert.Equal(served ? -140 : 0, scale.Needle);
            Assert.Equal(served ? 0.64 : 0, hatch.Position);
            Assert.Equal(served ? 1 : 0, flag.Position);
            Assert.Equal(0, scale.TwitchOffset);
            Assert.Equal(0, g.Log.Count);
            Mech.Run(g, 30);
            Assert.Equal(served, scale.Engaged);
        }

        [Fact]
        public void WeighIn_RestoredMidSwing_ContinuesIdentically()
        {
            var (a, ba, _, _, _, _) = Dl05();
            ba.X = BodyPlate;
            Mech.Run(a, 40);
            var (b, _, _, _, _, _) = Dl05("hatch");
            PlateKit.RoundTrip(a, b, 240);
            Assert.True(b.Get<WeighScale>("dl05.weighIn").Engaged);
        }

        // ---- PresenceStrip: DL-12 ------------------------------------------------------------------------------------------

        private static (MechanismGraph g, TestBody fig, TestBody coat, PresenceStrip strip, FollowerActuator gate) Dl12(string cp = "school")
        {
            bool reg = Checkpoint.Prototype(cp).Past("register");
            var fig = new TestBody("dl12.figure", reg ? 208.4 : 207.0);
            var coat = new TestBody("dl12.coat", 202.92, reg ? BodySupport.Placed : BodySupport.Floor);
            var strip = new PresenceStrip("dl12.strip", PresenceStripParams.Dl12Strip());
            var gate = new FollowerActuator("dl12.gate", FollowerParams.Dl12Gate());
            return (Mech.Graph(cp, fig, coat, strip, gate), fig, coat, strip, gate);
        }

        [Theory]
        [InlineData(208.4, 0.0, 207.0, true)]
        [InlineData(208.01, 0.0, 207.0, true)]
        [InlineData(208.0, 0.0, 207.0, false)]
        [InlineData(208.4, 0.05, 207.0, false)]
        [InlineData(205.0, 0.0, 208.16, true)]
        [InlineData(205.0, 0.0, 208.15, false)]
        [InlineData(205.0, 0.0, 208.64, true)]
        public void Strip_HimOnIt_OrTheFigureWithin025_L5382_L5383(double hx, double hy, double fx, bool present)
        {
            var (g, fig, _, strip, _) = Dl12();
            fig.X = fx;
            g.Step(Mech.Dt, On(hx, hy));
            Assert.Equal(present, strip.Present);
            Assert.Equal(present ? PresenceState.Present : PresenceState.Empty, strip.State);
            Assert.Equal(0, strip.Load);
        }

        [Fact]
        public void Strip_AsksForTheCoat06sAfterEachArrival_L5384_L5390()
        {
            var (g, _, _, strip, _) = Dl12();
            int ask = -1;
            g.Step(Mech.Dt, On(208.4));
            Assert.True(Mech.Emitted(g, "dl12.strip", PresenceEvent.Press));
            for (int k = 1; k <= 60; k++)
            {
                g.Step(Mech.Dt, On(208.4));
                var e = PlateKit.Find(g, "dl12.strip", (int)PresenceEvent.AskForCoat);
                if (e.HasValue) { ask = k; Assert.Equal(1, e.Value.Index); }
            }
            Assert.InRange(ask, 36, 37);
            Mech.Run(g, 10, On(205));
            int again = Mech.RunUntil(g, () => Mech.Emitted(g, "dl12.strip", PresenceEvent.AskForCoat), 200, On(208.4));
            Assert.Equal(2, PlateKit.Find(g, "dl12.strip", (int)PresenceEvent.AskForCoat).Value.Index);
            Assert.InRange(again, 37, 38);
            Assert.Equal(2, strip.PresentCount);
        }

        [Fact]
        public void Strip_NoVoiceFrom212_L5385()
        {
            var (g, fig, _, _, _) = Dl12();
            fig.X = 208.4;
            int asks = 0;
            for (int k = 0; k < 120; k++) { g.Step(Mech.Dt, On(212.0)); asks += PlateKit.Count(g, "dl12.strip", (int)PresenceEvent.AskForCoat); }
            Assert.Equal(0, asks);
        }

        [Fact]
        public void Strip_PresentWithTheCoat_Opens_ThanksOnce_GateTo13_L5391_L5400()
        {
            var (g, fig, coat, strip, gate) = Dl12();
            coat.Support = BodySupport.Placed;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(PresenceState.Empty, strip.State);
            fig.X = 208.4;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl12.strip", PresenceState.Open));
            Assert.True(Mech.Emitted(g, "dl12.strip", PresenceEvent.Thanks));
            Assert.Equal(1, strip.Load);
            int up = Mech.RunUntil(g, () => gate.Position >= 1.3);
            Assert.InRange(up, 155, 157);                             // 1.3 m at 0.5 m/s
            fig.X = 207.0;
            Mech.Run(g, 5);
            fig.X = 208.4;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.False(Mech.Emitted(g, "dl12.strip", PresenceEvent.Thanks));
        }

        [Theory]
        [InlineData("school", PresenceState.Empty, 0.0)]
        [InlineData("register", PresenceState.Open, 1.3)]
        public void Strip_ResetFromCheckpoint_NoReplayedThanks_L5233_L5235(string cp, PresenceState state, double gateY)
        {
            var (g, _, _, strip, gate) = Dl12(cp);
            Assert.Equal(state, strip.State);
            Assert.Equal(gateY, gate.Position, 12);
            for (int k = 0; k < 5; k++) { g.Step(Mech.Dt, On(210.0)); Assert.Empty(Mech.Events(g)); }
        }

        [Fact]
        public void Strip_RestoredMidWait_ContinuesIdentically()
        {
            var (a, _, _, _, _) = Dl12();
            Mech.Run(a, 20, On(208.4));
            var (b, _, _, _, _) = Dl12("register");
            PlateKit.RoundTrip(a, b, 60, k => On(208.4));
        }

        // ---- SeatRow: DL-15 ------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, TestBody a, TestBody b, TestSource chair, SeatRow seats, Door door) Dl15(string cp = "class6")
        {
            bool dismissed = Checkpoint.Prototype(cp).Past("dismissed");
            var a = new TestBody("dl15.figA", dismissed ? 296.82 : 289.2);
            var b = new TestBody("dl15.figB", dismissed ? 297.62 : 281.9);
            var chair = new TestSource("dl15.chair");
            var seats = new SeatRow("dl15.seats", SeatRowParams.Dl15Seats());
            var door = new Door("dl15.classDoor", DoorParams.Dl15ClassDoor());
            return (Mech.Graph(cp, a, b, chair, seats, door), a, b, chair, seats, door);
        }

        [Fact]
        public void Seats_LampPerDockedFigure_AndTheChair_L5723_L5726()
        {
            var (g, a, b, chair, seats, _) = Dl15();
            a.X = 283.2 + 0.029;
            g.Step(Mech.Dt, PlayerPose.Away);
            var e = PlateKit.Find(g, "dl15.seats", (int)SeatRowEvent.Lamp).Value;
            Assert.Equal(0, e.Index);
            Assert.True(seats.Lit(0));
            b.X = 284.6 - 0.031;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.False(seats.Lit(1));
            b.Support = BodySupport.Carrier; b.X = 284.6;           // not on the floor
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.False(seats.Lit(1));
            chair.Engaged = true;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(seats.Lit(2));
            Assert.Equal(SeatRowState.Waiting, seats.State);
        }

        [Fact]
        public void Seats_AllLitFor16s_Dismisses_DoorOpensOver16s_L5728_L5737()
        {
            var (g, a, b, chair, seats, door) = Dl15();
            a.X = 283.2; b.X = 284.6;
            g.Step(Mech.Dt, PlayerPose.Away);
            chair.Engaged = true;
            Mech.Run(g, 50);
            chair.Engaged = false;                                    // stood up: start again
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl15.seats", SeatRowState.Waiting));
            chair.Engaged = true;
            int n = Mech.RunUntil(g, () => seats.Engaged);
            Assert.InRange(n, 97, 98);                                // clock − allSince > 1.6
            var bell = PlateKit.Find(g, "dl15.seats", (int)SeatRowEvent.Bell).Value;
            Assert.Equal(0.7, bell.Value);
            Assert.True(Mech.Entered(g, "dl15.classDoor", DoorState.Opening));
            Assert.InRange(Mech.RunUntil(g, () => door.Engaged), 95, 96);
            chair.Engaged = false;
            Mech.Run(g, 10);
            Assert.True(seats.Engaged);
        }

        [Theory]
        [InlineData("class6", false, 0.0)]
        [InlineData("dismissed", true, 1.0)]
        public void Seats_ResetFromCheckpoint_L5540_L5546(string cp, bool dismissed, double door)
        {
            var (g, _, _, _, seats, d) = Dl15(cp);
            Assert.Equal(dismissed, seats.Engaged);
            Assert.Equal(door, d.Position);
            Assert.False(seats.Lit(0) || seats.Lit(1) || seats.Lit(2));
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Seats_RestoredMidHold_ContinuesIdentically()
        {
            var (a, fa, fb, ca, _, _) = Dl15();
            fa.X = 283.2; fb.X = 284.6; ca.Engaged = true;
            Mech.Run(a, 40);
            var (b, _, _, _, _, _) = Dl15();
            PlateKit.RoundTrip(a, b, 120);
            Assert.True(b.Get<SeatRow>("dl15.seats").Engaged);
        }

        // ---- PlateDoor: DL-04 bay door -------------------------------------------------------------------------------------

        private static (MechanismGraph g, TestSource cradle, LoadPlate plate, PlateDoor door) Dl04Door(bool seated = false)
        {
            var cradle = new TestSource("dl04.cradle") { Engaged = seated };
            var plate = new LoadPlate("dl04.bayPlate", LoadPlateParams.Dl04BayPlate());
            var door = new PlateDoor("dl04.bayDoor", PlateDoorParams.Dl04BayDoor());
            return (Mech.Graph(seated ? "bay" : "start", cradle, plate, door), cradle, plate, door);
        }

        [Fact]
        public void BayDoor_HimOnThePlate_Opens11s_Closes05s_L4786_L4815()
        {
            var (g, _, plate, door) = Dl04Door();
            g.Step(Mech.Dt, On(44.05, 0.09));
            Assert.True(plate.Engaged);
            Assert.True(Mech.Entered(g, "dl04.bayDoor", PlateDoorState.Opening));
            int open = Mech.RunUntil(g, () => door.Engaged, pose: On(44.5)) + 1;
            Assert.InRange(open, 66, 67);
            Assert.Equal(1.7, door.Position);
            Mech.Run(g, 20, On(44.5));
            Assert.Equal(1.0, door.Open01);                            // holds (the prototype saws 0.03 below)
            Assert.Equal(PlateDoorState.Open, door.State);
            int closed = Mech.RunUntil(g, () => door.State == PlateDoorState.Closed, pose: On(45.0));
            Assert.InRange(closed, 30, 31);
            g.Step(Mech.Dt, On(44.5, 0.1));
            Assert.False(plate.Engaged);
        }

        [Fact]
        public void BayDoor_TheSeatedCourierHoldsIt_Opens22s_L4813_L4814()
        {
            var (g, cradle, _, door) = Dl04Door();
            cradle.Engaged = true;
            int open = Mech.RunUntil(g, () => door.Engaged);
            Assert.InRange(open, 132, 133);
            Mech.Run(g, 30);
            Assert.True(door.Engaged);
        }

        [Fact]
        public void BayDoor_ResetAtBay_Open_L4097()
        {
            var (g, _, _, door) = Dl04Door(seated: true);
            Assert.Equal(PlateDoorState.Open, door.State);
            Assert.Equal(1.7, door.Position);
            Assert.True(door.Want);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void BayDoor_RestoredMidOpening_ContinuesIdentically()
        {
            var (a, _, _, _) = Dl04Door();
            Mech.Run(a, 30, On(44.5));
            var (b, _, _, _) = Dl04Door(seated: true);
            PlateKit.RoundTrip(a, b, 90, k => k < 50 ? On(44.5) : PlayerPose.Away);
        }

        // ---- Determinism ---------------------------------------------------------------------------------------------------

        [Fact]
        public void TwoRuns_WithTheSameInputs_AreBitIdentical()
        {
            var traces = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var (g, body, drum, _, _, _) = Dl05();
                var t = traces[r] = new List<string>();
                for (int k = 0; k < 400; k++)
                {
                    drum.X = k < 100 ? Drum0 + k * 0.014 : k < 200 ? DrumPark : DrumPark;
                    body.X = k < 200 ? Body0 : Math.Min(BodyPlate, Body0 + (k - 200) * 0.012);
                    g.Step(Mech.Dt, k % 90 < 40 ? On(54.2) : PlayerPose.Away);
                    t.Add(Mech.Dump(g));
                }
            }
            Assert.Equal(traces[0], traces[1]);
        }
    }
}
