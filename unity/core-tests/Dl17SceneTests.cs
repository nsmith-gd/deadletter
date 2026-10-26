using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Water;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-17 A Different Lesson's test rig as a scene: valve, three sluices, tank, beds, float latch and the stair door,
    /// driven by the real motor and resolver in pipeline order (motor #4, then the graph; §3.1), with the prototype's
    /// timings (§4.13i, L5789–L5794, L6193–L6259).
    /// </summary>
    public class Dl17SceneTests
    {
        private const double Dt = Mech.Dt;

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly SluiceValve Valve;
            public readonly Sluice[] Sluices = new Sluice[3];
            public readonly SluiceRig Rig;
            public readonly FloatLatch Latch;
            public readonly Door Door;
            public readonly D17Motor Motor;
            public readonly List<string> Trace = new List<string>();
            public readonly List<MechanismEvent> Log = new List<MechanismEvent>();

            public Scene(double x = 336.3)
            {
                Valve = G.Add(new SluiceValve("dl17.valve", SluiceValveParams.Dl17Valve()));
                for (int i = 0; i < 3; i++) Sluices[i] = G.Add(new Sluice("dl17.sluice" + "ABC"[i], SluiceParams.Dl17Sluice(i)));
                Rig = G.Add(new SluiceRig("dl17.rig", SluiceRigParams.Dl17Rig()));
                Latch = G.Add(new FloatLatch("dl17.latch", FloatLatchParams.Dl17Latch()));
                Door = G.Add(new Door("dl17.stairDoor", DoorParams.Dl17StairDoor()));
                G.Build();
                G.Reset(Checkpoint.Prototype("kitchen"));
                var resolver = new InteractionResolver();
                resolver.Register(Valve);
                foreach (var s in Sluices) resolver.Register(s);
                Motor = Sim.Make(BoxWorld.Flat(320, 350), x, 0, resolver);   // the workshop floor
            }

            public void Step(MotorInput input)
            {
                Motor.Step(input, Dt);
                G.Step(Dt, Mech.Pose(Motor));
                Log.AddRange(Mech.Events(G));
                Trace.Add(Sim.Snapshot(Motor) + "#" + Mech.Dump(G));
            }

            public void Idle(int steps) { for (int i = 0; i < steps; i++) Step(Sim.Move(0)); }

            public void WalkTo(double x)
            {
                for (int i = 0; i < 1200 && Math.Abs(Motor.X - x) > 0.04; i++) Step(Sim.Move(Math.Sign(x - Motor.X) * 0.4));
                Idle(30);
                Assert.InRange(Motor.X, x - 0.12, x + 0.12);
            }

            /// <summary>Use on <paramref name="target"/> (it must be what Use would pick), then wait out the act.</summary>
            public void Use(IInteractable target)
            {
                Assert.True(Motor.PreviewUse(out var c));
                Assert.Same(target, c.Target);
                Step(Sim.Use());
                for (int i = 0; i < 600 && Motor.IsActing; i++) Step(Sim.Move(0));
                Assert.False(Motor.IsActing);
            }

            public int Count(MechanismId id, SluiceRigEvent e) => Log.FindAll(x => x.Id == id && x.Kind == MechanismEventKind.Event && x.Code == (int)e).Count;
        }

        /// <summary>The whole scene: a shared run fails, then B alone lifts the latch and the door opens.</summary>
        private static Scene Play(Action<Scene, string> at = null)
        {
            var s = new Scene();
            s.Use(s.Valve);                                                                     // all three open: shared
            at?.Invoke(s, "shared");
            for (int i = 0; i < 600 && s.Rig.Engaged; i++) s.Step(Sim.Move(0));
            at?.Invoke(s, "failed");
            s.WalkTo(337.4);
            s.Use(s.Sluices[0]);
            s.WalkTo(338.75);
            s.Use(s.Sluices[2]);
            s.WalkTo(336.35);
            for (int i = 0; i < 900 && s.Rig.State != SluiceRigState.Ready; i++) s.Step(Sim.Move(0));
            s.Use(s.Valve);                                                                     // B alone: bed 1
            at?.Invoke(s, "solo");
            for (int i = 0; i < 600 && s.Door.State != DoorState.Open; i++) s.Step(Sim.Move(0));
            return s;
        }

        [Fact]
        public void ASharedRunFails_ThenSluiceBAlone_LiftsTheFloatLatch_AndTheStairDoorOpens_L6193_L6259_L5789()
        {
            double sharedMaxDeg = 0;
            var s = Play((sc, phase) =>
            {
                if (phase == "shared")
                {
                    Assert.Equal(SluiceRigState.Running, sc.Rig.State);
                    for (int i = 0; i < 600 && sc.Rig.Engaged; i++) { sc.Step(Sim.Move(0)); sharedMaxDeg = Math.Max(sharedMaxDeg, sc.Latch.ArmDeg); }
                }
                if (phase == "failed")
                {
                    Assert.Equal(1, sc.Count("dl17.rig", SluiceRigEvent.Failed));
                    Assert.Equal(FloatLatchState.Down, sc.Latch.State);
                    for (int b = 0; b < 3; b++) Assert.InRange(sc.Rig.Bed(b), 0.34, 1.06 / 3);
                }
                if (phase == "solo")
                {
                    Assert.True(sc.Rig.Engaged);
                    Assert.False(sc.Sluices[0].Engaged);
                    Assert.True(sc.Sluices[1].Engaged);
                    Assert.False(sc.Sluices[2].Engaged);
                    int started = sc.Log.FindLastIndex(e => e.Id == "dl17.rig" && e.Code == (int)SluiceRigEvent.Started && e.Kind == MechanismEventKind.Event);
                    long t0 = sc.Log[started].Tick;
                    int latchedAt = -1, opening = -1, open = -1;
                    for (int i = 0; i < 900 && open < 0; i++)
                    {
                        sc.Step(Sim.Move(0));
                        if (Mech.Entered(sc.G, "dl17.latch", FloatLatchState.Latched)) latchedAt = (int)(sc.G.Tick - 1 - t0);
                        if (Mech.Entered(sc.G, "dl17.stairDoor", DoorState.Opening)) opening = (int)(sc.G.Tick - 1 - t0);
                        if (Mech.Entered(sc.G, "dl17.stairDoor", DoorState.Open)) open = (int)(sc.G.Tick - 1 - t0);
                    }
                    Assert.InRange((latchedAt + 1) * Dt, 0.95 / 1.06 * 6 - Dt, 0.95 / 1.06 * 6 + Dt);   // bed 1 ≥ 0.95, L6258
                    Assert.InRange((opening - latchedAt) * Dt, 0.8, 0.8 + 2 * Dt + 1e-9);                // 0.8 s after the latch, L5789
                    Assert.InRange((open - opening) * Dt, 1.8 - Dt - 1e-9, 1.8 + Dt + 1e-9);             // over 1.8 s, L5794
                }
            });
            Assert.InRange(sharedMaxDeg, 5, 15);                     // a shared run lifts the latch part-way (L6314)
            Assert.Equal(DoorState.Open, s.Door.State);
            Assert.Equal(FloatLatchState.Latched, s.Latch.State);
            Assert.Equal(70, s.Latch.ArmDeg, 9);
            Assert.Equal(2, s.Count("dl17.rig", SluiceRigEvent.Started));
            Assert.Equal(1, s.Count("dl17.rig", SluiceRigEvent.Failed));
        }

        [Fact]
        public void TheValveRefusesUntilTheTankRefills_L6203_L6255()
        {
            var s = new Scene();
            s.Use(s.Valve);
            for (int i = 0; i < 600 && s.Rig.Engaged; i++) s.Step(Sim.Move(0));
            s.Idle(30);
            s.Use(s.Valve);
            Assert.Equal(1, s.Count("dl17.rig", SluiceRigEvent.RefusedLow));
            Assert.True(s.Rig.Refilling);
        }

        [Fact]
        public void SnapshotMidRun_RestoresAndContinuesBitIdentically()
        {
            var a = new Scene();
            a.Use(a.Valve);
            a.Idle(90);
            Assert.Equal(SluiceRigState.Running, a.Rig.State);
            var b = new Scene(330);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 500; k++)                         // the run ends; the tank refills
            {
                a.Step(Sim.Move(0));
                b.G.Step(Dt, Mech.Pose(a.Motor));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
            Assert.Equal(SluiceRigState.Refilling, b.Rig.State);
        }

        [Fact]
        public void TwoRunsOfTheScene_WithTheSameInputs_AreBitIdentical()
        {
            var a = Play();
            var b = Play();
            Assert.Equal(a.Trace, b.Trace);
            Assert.Equal(DoorState.Open, b.Door.State);
        }
    }
}
