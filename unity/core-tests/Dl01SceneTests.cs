using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-01 The Wake as a scene: relay, latch → shutter, crank → door, driven by the real motor and resolver in the
    /// pipeline order (motor #4, then the graph #5–#6; §3.1), with the prototype's timings (§4.13c–e, §5).
    /// </summary>
    public class Dl01SceneTests
    {
        private const double Dt = Mech.Dt;

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly PulseSequencer Relay;
            public readonly Latch Latch;
            public readonly Door Shutter;
            public readonly CrankActuator Crank;
            public readonly Door Door;
            public readonly D17Motor Motor;

            public Scene(string checkpoint, double x, bool flinch = true)
            {
                var latch = LatchParams.Dl01Latch();
                if (!flinch) latch.FlinchClip = null;
                Relay = G.Add(new PulseSequencer("dl01.relay", PulseParams.Dl01Relay()));     // #5 relay pulse
                Latch = G.Add(new Latch("dl01.latch", latch));                               // #6 updateMechanisms
                Shutter = G.Add(new Door("dl01.shutter", DoorParams.Dl01Shutter()));
                Crank = G.Add(new CrankActuator("dl01.crank", CrankParams.Dl01Crank()));
                Door = G.Add(new Door("dl01.door", DoorParams.Dl01Door()));
                G.Build();
                G.Reset(Checkpoint.Prototype(checkpoint));
                var resolver = new InteractionResolver();
                resolver.Register(Latch);
                resolver.Register(Crank);
                Motor = Sim.Make(BoxWorld.Flat(), x, 0, resolver);
            }

            /// <summary>One pipeline step. Returns the clip frame the act read this step (-1 outside a clip).</summary>
            public double Step(MotorInput input)
            {
                double f = Motor.IsActing ? Motor.ClipTime * 24 : -1;
                Motor.Step(input, Dt);
                G.Step(Dt, Mech.Pose(Motor));
                return f;
            }
        }

        [Fact]
        public void PullingTheLatch_ReleasesAtPullF31_AndTheShutterSwingsTheSameStep_L1870_L1874_L1691()
        {
            var s = new Scene("start", 2.7);
            Assert.True(s.Motor.PreviewUse(out var c));
            Assert.Same(s.Latch, c.Target);
            s.Step(Sim.Use());
            bool crouchedApproach = false, crouchedFlinch = true;
            int release = -1, cue = -1, open = -1, actEnd = -1, flinch = -1;
            for (int i = 1; i <= 600; i++)
            {
                double f = s.Step(Sim.Move(0));
                if (s.Motor.IsActing && s.Motor.Clip == ClipNames.CrouchWalk) crouchedApproach |= s.Motor.Crouched;
                if (Mech.Entered(s.G, "dl01.latch", LatchState.Released))
                {
                    release = i;
                    Assert.Equal("Pull", s.Motor.Clip);
                    Assert.InRange(f, 31, 31.4 + 1e-9);
                    Assert.Equal(3.0, s.Motor.X, 9);
                    Assert.True(Mech.Entered(s.G, "dl01.shutter", DoorState.Opening));   // same tick: t = 0
                    Assert.Equal(15.6, s.Shutter.Position, 12);
                }
                if (Mech.Emitted(s.G, "dl01.shutter", DoorEvent.Cue)) cue = i;
                if (Mech.Entered(s.G, "dl01.shutter", DoorState.Open)) open = i;
                if (flinch < 0 && s.Motor.Clip == ClipNames.Flinch) flinch = i;
                if (flinch > 0 && actEnd < 0 && s.Motor.IsActing) crouchedFlinch &= s.Motor.Crouched && s.Motor.ActPart == 1;
                if (actEnd < 0 && release > 0 && !s.Motor.IsActing) actEnd = i;
            }
            Assert.True(crouchedApproach);
            Assert.True(release > 0);
            Assert.Equal(release + 34, cue);                      // the thud at 0.56 s (L1683)
            Assert.Equal(release + 54, open);                     // settled at 0.9 s
            Assert.InRange((flinch - release) * 24.0 / 60, 39 - 31.4, 39 - 31 + 0.8);   // Pull f39 chains Flinch (L1875)
            Assert.Equal(96, actEnd - flinch);                    // 1.6 s of Flinch, still crouched, then the act ends (L1876)
            Assert.True(crouchedFlinch);
            Assert.False(s.Motor.Crouched);
            Assert.Equal(15.0, s.Shutter.Position);
            Assert.InRange(s.Latch.LeverDeg, 71.5, 72);           // leverAngleAt(39), L1872
            Assert.False(s.Motor.PreviewUse(out _));              // nothing else to use at the latch
        }

        [Fact]
        public void CrankingTheDoor_FiveStrokesOfOneSecond_RaiseItOneMetre_L1877_L1890_L7957()
        {
            var s = new Scene("hall", 9.4);
            Assert.True(s.Motor.PreviewUse(out var c));
            Assert.Same(s.Crank, c.Target);
            s.Step(Sim.Use());
            var strokes = new List<double>();
            int done = -1;
            double doneFrame = -1;
            for (int i = 1; i <= 900 && done < 0; i++)
            {
                double f = s.Step(Sim.Move(0));
                foreach (var e in Mech.Events(s.G))
                    if (e.Id == "dl01.crank" && e.Kind == MechanismEventKind.Event && e.Code == (int)CrankEvent.Stroke) strokes.Add(f);
                if (Mech.Entered(s.G, "dl01.crank", CrankState.Done)) { done = i; doneFrame = f; }
                Assert.Equal(s.Crank.Position * 1.0, s.Door.Position, 12);
            }
            Assert.Equal(5, strokes.Count);
            for (int k = 0; k < 5; k++) Assert.InRange(strokes[k], 24 * (k + 1) - 1e-6, 24 * (k + 1) + 0.4 + 1e-6);
            Assert.InRange(doneFrame, 120 - 1e-6, 120.4 + 1e-6);
            Assert.Equal(1.0, s.Door.Position);
            Assert.Equal(DoorState.Open, s.Door.State);
            Sim.RunUntil(s.Motor, Sim.Move(0), m => { s.G.Step(Dt, Mech.Pose(m)); return !m.IsActing; }, 300);
            Assert.False(s.Motor.IsActing);
            Assert.False(s.Motor.PreviewUse(out _));              // doorOpen = 1: the crank no longer answers (L1813)
        }

        [Theory]
        [InlineData("start", LatchState.Locked, DoorState.Closed, 0.0, 1.56, CrankState.Idle, 0.0)]
        [InlineData("shutter", LatchState.Released, DoorState.Open, 15.0, 0.12, CrankState.Idle, 0.0)]
        [InlineData("hall", LatchState.Released, DoorState.Open, 15.0, 0.12, CrankState.Idle, 0.0)]
        [InlineData("door", LatchState.Released, DoorState.Open, 15.0, 0.12, CrankState.Done, 1.0)]
        [InlineData("room", LatchState.Released, DoorState.Open, 15.0, 0.12, CrankState.Done, 1.0)]
        public void ResetFromCheckpoint_DerivesEveryMechanism_L7976_L8024(string cp, LatchState latch, DoorState shutter,
            double shutterDeg, double weightY, CrankState crank, double door)
        {
            var s = new Scene(cp, 1.0);
            Assert.Equal(latch, s.Latch.State);
            Assert.Equal(shutter, s.Shutter.State);
            Assert.Equal(shutterDeg, s.Shutter.Position);
            Assert.Equal(weightY, Door.ShutterCounterweightY(s.Shutter.Elapsed), 12);
            Assert.Equal(crank, s.Crank.State);
            Assert.Equal(door, s.Door.Position);
            Assert.Equal(door >= 1 ? DoorState.Open : DoorState.Closed, s.Door.State);
            Assert.Equal(480, s.Relay.Units, 9);                  // play starts after the 480-frame opening
        }

        [Fact]
        public void Respawn_KeepsTheRelayPhase_AndRebuildsTheRest_L8095()
        {
            var s = new Scene("start", 2.7);
            s.Step(Sim.Use());
            for (int i = 0; i < 400; i++) s.Step(Sim.Move(0));
            double units = s.Relay.Units;
            Assert.Equal(LatchState.Released, s.Latch.State);
            s.G.Reset(Checkpoint.Prototype("start"));
            Assert.Equal(units, s.Relay.Units);
            Assert.Equal(LatchState.Locked, s.Latch.State);
            Assert.Equal(0, s.Shutter.Position);
        }

        [Fact]
        public void SnapshotMidSwing_RestoresAndContinuesBitIdentically()
        {
            var a = new Scene("start", 2.7, flinch: false);       // the act is over 0.4 s in, so the copy needs no act frames
            a.Step(Sim.Use());
            int i = 0;
            while (a.Latch.State == LatchState.Locked && i++ < 600) a.Step(Sim.Move(0));
            for (int k = 0; k < 24; k++) a.Step(Sim.Move(0));    // 0.4 s into the swing; the pull is over
            Assert.Equal(DoorState.Opening, a.Shutter.State);
            Assert.False(a.Motor.IsActing);

            var b = new Scene("door", 7.0);                       // any state: the snapshot overwrites it
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 120; k++)
            {
                a.Step(Sim.Move(0));
                b.G.Step(Dt, Mech.Pose(a.Motor));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
            Assert.Equal(DoorState.Open, b.Shutter.State);
        }

        [Fact]
        public void TwoRunsOfTheScene_WithTheSameInputs_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var s = new Scene("start", 2.7);
                s.G.Calm = false;
                var trace = runs[r] = new List<string>();
                MotorInput Input(int step) =>
                    step == 0 || step == 1100 ? Sim.Use() : step > 500 && step < 1100 && s.Motor.X < 9.4 ? Sim.Move(1) : Sim.Move(0);
                for (int step = 0; step < 1900; step++)
                {
                    s.Step(Input(step));
                    trace.Add(Sim.Snapshot(s.Motor) + "#" + Mech.Dump(s.G));
                }
                Assert.Equal(DoorState.Open, s.Shutter.State);
                Assert.Equal(CrankState.Done, s.Crank.State);
            }
            Assert.Equal(runs[0], runs[1]);
        }
    
        /// <summary>
        /// U-14 (DL-01 §8 test 2, §9 Recovery): play the scene with the real motor, saving at each checkpoint as the
        /// prototype sets it (start at the handover; shutter on the release, L1677; hall past the pit, L2065; door on
        /// the crank's last stroke, L1890). At each one, quit and continue in a fresh scene: every mechanism comes back
        /// exactly (bar the tick), then steps on bit-identically with the original.
        /// </summary>
        [Fact]
        public void SaveAndContinue_AtEveryCheckpoint_RestoresTheExactState()
        {
            var s = new Scene("start", 2.7);
            var fs = new MemoryFileSystem();
            var svc = SaveKit.Service(s.G, fs, "DL-01");
            svc.NewGame();                                                    // control handover: start
            var saved = new List<(string cp, string dump, byte[] bytes)> { ("start", SaveKit.Dump(s.G), (byte[])fs.Files["slot0.dls"].Clone()) };

            void Check(string cp)
            {
                Assert.True(svc.Reach(cp));
                saved.Add((cp, SaveKit.Dump(s.G), (byte[])fs.Files["slot0.dls"].Clone()));
            }

            s.Step(Sim.Use());
            for (int i = 0; i < 600 && s.Latch.State == LatchState.Locked; i++) s.Step(Sim.Move(0));
            Check("shutter");
            Assert.Equal(DoorState.Opening, s.Shutter.State);                 // mid-swing: kept exactly
            for (int i = 0; i < 1200 && s.Motor.X < 8.35; i++) s.Step(s.Motor.IsActing ? Sim.Move(0) : Sim.Move(1));
            Assert.True(s.Motor.X >= 8.35);
            Check("hall");
            for (int i = 0; i < 600 && Math.Abs(s.Motor.X - 9.4) > 0.04; i++) s.Step(Sim.Move(Math.Sign(9.4 - s.Motor.X) * 0.4));
            for (int i = 0; i < 60; i++) s.Step(Sim.Move(0));
            s.Step(Sim.Use());
            for (int i = 0; i < 900 && s.Crank.State != CrankState.Done; i++) s.Step(Sim.Move(0));
            Check("door");
            Assert.Equal(DoorState.Open, s.Door.State);
            Assert.Equal(new[] { "start", "shutter", "hall", "door" }, saved.ConvertAll(x => x.cp));

            foreach (var (cp, dump, bytes) in saved)
            {
                var copy = new MemoryFileSystem();
                copy.Files["slot0.dls"] = bytes;
                var b = new Scene("room", 5.0);                               // any state: the save overwrites it
                SaveKit.Continue(b.G, copy, "DL-01", cp, dump);
                Assert.Equal(cp == "start" ? LatchState.Locked : LatchState.Released, b.Latch.State);
                Assert.Equal(cp == "door" ? CrankState.Done : CrankState.Idle, b.Crank.State);

                var a = new Scene("start", 2.7);                              // the original, reloaded in-session
                var svcA = SaveKit.Service(a.G, copy, "DL-01");
                Assert.True(svcA.TryContinue());
                for (int k = 0; k < 120; k++)
                {
                    a.G.Step(Dt, Mech.Pose(a.Motor));
                    b.G.Step(Dt, Mech.Pose(a.Motor));
                    Assert.Equal(SaveKit.Dump(a.G), SaveKit.Dump(b.G));
                }
            }
        }

        [Fact]
        public void Respawn_AfterTheHall_RestoresTheHallSnapshot_NotTheLaterState()
        {
            var s = new Scene("start", 2.7);
            var svc = SaveKit.Service(s.G, new MemoryFileSystem(), "DL-01");
            svc.NewGame();
            s.Step(Sim.Use());
            for (int i = 0; i < 600 && s.Latch.State == LatchState.Locked; i++) s.Step(Sim.Move(0));
            svc.Reach("shutter");
            for (int i = 0; i < 120; i++) s.Step(Sim.Move(0));
            string atHall = null;
            for (int i = 0; i < 1200 && s.Motor.X < 8.35; i++) s.Step(Sim.Move(1));
            Assert.True(svc.Reach("hall"));
            atHall = SaveKit.Dump(s.G);
            for (int i = 0; i < 300; i++) s.Step(Sim.Move(0));
            Assert.NotEqual(atHall, SaveKit.Dump(s.G));                     // the relay has moved on
            svc.Reload();
            Assert.Equal(atHall, SaveKit.Dump(s.G));
            Assert.Equal(DoorState.Open, s.Shutter.State);                    // the solved shutter stays solved
        }

        [Theory]
        [InlineData("shutter", LatchState.Released, DoorState.Open, CrankState.Idle)]
        [InlineData("hall", LatchState.Released, DoorState.Open, CrankState.Idle)]
        [InlineData("door", LatchState.Released, DoorState.Open, CrankState.Done)]
        public void Continue_WithoutASnapshot_DerivesTheSolvedStates_L8022_L8023(string cp, LatchState latch, DoorState shutter, CrankState crank)
        {
            var fs = new MemoryFileSystem();
            new AtomicFileStore(fs).Save(0, new SaveModel { Checkpoint = cp, Scene = "DL-01" });   // e.g. migrated from v1
            var b = new Scene("start", 2.7);
            var svc = SaveKit.Service(b.G, fs, "DL-01");
            Assert.True(svc.TryContinue());
            Assert.False(svc.RestoredSnapshot);
            Assert.Equal(latch, b.Latch.State);
            Assert.Equal(shutter, b.Shutter.State);
            Assert.Equal(crank, b.Crank.State);
        }
}
}
