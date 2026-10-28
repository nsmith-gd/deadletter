using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-11b (#22): riding (board / ride / alight on DL-06's carriers; ride sync at step #9 for carriers and lifts,
    /// <see cref="MotorSync"/>), the belt's carry (<see cref="ILaneConveyor"/>), and the probes mechanisms answer for the
    /// lane (crates on the belt, DL-18's swept volumes, <see cref="SweptVolumeProbe"/>), with the real motor.
    /// </summary>
    public class RideAndLaneTests
    {
        private const double Dt = Mech.Dt;

        /// <summary>
        /// A box lane plus the probes of mechanisms, as a scene's lane geometry folds its contributors in: each surface and
        /// ceiling probe sees the boxes' answer and may raise (lower) it; the conveyors add up.
        /// </summary>
        private sealed class TestLane : IMotorWorld, ILaneConveyor
        {
            private readonly BoxWorld _boxes;
            private readonly List<Func<double, double, double, double>> _surface = new List<Func<double, double, double, double>>();
            private readonly List<Func<double, double, double, double>> _ceiling = new List<Func<double, double, double, double>>();
            private readonly List<Func<double, double, double>> _carry = new List<Func<double, double, double>>();

            public TestLane(BoxWorld boxes) { _boxes = boxes; }

            public TestLane Surface(Func<double, double, double, double> f) { _surface.Add(f); return this; }
            public TestLane Ceiling(Func<double, double, double, double> f) { _ceiling.Add(f); return this; }
            public TestLane Carry(Func<double, double, double> f) { _carry.Add(f); return this; }

            /// <summary>A swept volume (a folding leaf), standable while <paramref name="standable"/> is engaged.</summary>
            public TestLane Swept(ISweptVolume v, IEngageable standable)
                => Surface((x, y, h) => SweptVolumeProbe.Surface(v, standable.Engaged, x, h))
                  .Ceiling((x, y, h) => SweptVolumeProbe.Ceiling(v, standable.Engaged, x, y, h));

            public double SurfaceAt(double x, double refY)
            {
                double h = _boxes.SurfaceAt(x, refY);
                foreach (var f in _surface) h = f(x, refY, h);
                return h;
            }

            public double CeilingAt(double x, double refY)
            {
                double h = _boxes.CeilingAt(x, refY);
                foreach (var f in _ceiling) h = f(x, refY, h);
                return h;
            }

            public void Limits(double x, double y, out double left, out double right) => _boxes.Limits(x, y, out left, out right);
            public bool IsRamp(double x) => _boxes.IsRamp(x);
            public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
                => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);

            public double CarryAt(double x, double y)
            {
                double v = 0;
                foreach (var f in _carry) v += f(x, y);
                return v;
            }
        }

        private static BoxWorld Floor(double x0, double x1, double top)
        {
            var w = new BoxWorld { LeftLimit = x0, RightLimit = x1 };
            w.AddSolid(x0 - 1, x1 + 1, top);
            return w;
        }

        // ---- Carriers: board, ride, alight (L2854–L2994) --------------------------------------------------------------

        private sealed class LineScene
        {
            public readonly TestSource Belt = new TestSource("dl06.stopLever") { Engaged = true };
            public readonly TestSource Points;
            public readonly CarrierLine Line = new CarrierLine("dl06.line", CarrierLineParams.Dl06Line());
            public readonly MechanismGraph G;
            public readonly D17Motor M;
            public readonly List<string> Beats = new List<string>();

            public LineScene(bool exit, double x)
            {
                Points = new TestSource("dl06.points") { Engaged = exit };
                G = Mech.Graph("scanned", Belt, Points, Line);
                var r = new InteractionResolver();
                r.Register(Line.Rider);
                var w = BoxWorld.Flat(60, 80);
                w.AddSolid(71.85, 81, 1.6);                                    // the gallery (GALLERY.h)
                M = Sim.Make(w, x, 0, r);
            }

            /// <summary>#4 motor, #6 the line, #9 ride sync.</summary>
            public void Step(MotorInput i)
            {
                M.Step(i, Dt);
                G.Step(Dt, PlayerPose.Of(M));
                M.SyncRide();
                foreach (var e in M.Events)
                    if (e.Kind == MotorEventKind.Mounted || e.Kind == MotorEventKind.Alighted || e.Kind == MotorEventKind.ActStart) Beats.Add(e.Kind + ":" + e.Name);
            }

            public int Until(MotorInput i, Func<bool> f, int max = 3000)
            {
                for (int k = 1; k <= max; k++) { Step(i); if (f()) return k; }
                return -1;
            }

            public Carrier First => Line.Count > 0 ? Line.At(0) : null;
        }

        [Fact]
        public void Board_UseBesideTheDockedCarrier_HopsOnAlongTheArc_RidesItToTheLanding_AlightsOntoTheGallery_L2875_L2950_L2970()
        {
            var s = new LineScene(exit: true, x: 64.3);
            s.Until(Sim.Move(0), () => s.First != null && s.First.State == CarrierState.Dock);
            var c = s.First;
            Assert.True(s.M.PreviewUse(out var cand));
            Assert.Equal(Verb.Board, cand.Verb);
            Assert.Equal(c.Seq, cand.Token);
            s.Step(Sim.Use());
            double peak = 0;
            int mounted = s.Until(Sim.Move(0), () => { peak = Math.Max(peak, s.M.Y); return s.M.Ride != null; }, 200);
            Assert.InRange(mounted * 24.0 / 60, 22.6, 23.4);                    // Hop f23 (L2887)
            Assert.InRange(peak, 0.38, 0.38 + 0.14 + 1e-9);                     // the arc over the floor → the carrier's floor
            Assert.Equal(MotorState.Riding, s.M.State);
            Assert.Equal(ClipNames.Ride, s.M.Clip);
            s.Step(Sim.Move(0));
            Assert.True(c.Ridden);
            Assert.Same(c, s.Line.Ride);
            for (int k = 0; k < 400; k++)                                      // ride sync: on the carrier every step (L2961)
            {
                s.Step(Sim.Move(k % 2 == 0 ? 1 : -1));
                Assert.Equal(c.Position, s.M.X, 12);
                Assert.Equal(c.RideY, s.M.Y, 12);
                Assert.Equal(0.55, s.M.Z, 12);
            }
            s.Until(Sim.Move(0), () => c.State == CarrierState.Unload);
            int off = s.Until(Sim.Move(0), () => s.M.Ride == null && !s.M.IsActing, 300);
            Assert.True(off > 0);
            Assert.Contains("ActStart:Alight", s.Beats);
            Assert.Contains("Alighted:landing", s.Beats);
            Assert.Equal(72.7, s.M.X, 9);
            Assert.Equal(1.6, s.M.Y, 9);                                       // onto the gallery (L2953)
            Assert.Equal(0, s.M.Z);
            Assert.True(s.M.Grounded);
            s.Step(Sim.Move(0));
            Assert.False(c.Ridden);
            Assert.Null(s.Line.Ride);
        }

        [Fact]
        public void Board_AStandingJumpBesideACarrier_HopsOn_JumpAgainOnTheFloor_HopsOff_L1964_L2971()
        {
            var s = new LineScene(exit: false, x: 64.2);
            s.Until(Sim.Move(0), () => s.First != null && s.First.State == CarrierState.Dock);
            var c = s.First;
            s.Step(Sim.Jump(0));                                                // a standing jump boards (L1964)
            Assert.Equal(Verb.Board, s.M.ActVerb);
            s.Until(Sim.Move(0), () => s.M.Ride != null, 200);
            s.Until(Sim.Move(0), () => c.State == CarrierState.Move, 400);
            s.Step(Sim.Move(0));
            double x = s.M.X;
            s.Step(Sim.Jump(0));                                                // on the floor line, moving: he hops off where he is
            Assert.Equal(Verb.Alight, s.M.ActVerb);
            Assert.Null(s.M.Ride);
            s.Until(Sim.Move(0), () => !s.M.IsActing, 100);
            Assert.Equal(x, s.M.X, 9);
            Assert.Equal(0, s.M.Y, 9);
            Assert.Contains("Alighted:hop", s.Beats);
            s.Step(Sim.Move(0));
            Assert.False(c.Ridden);
        }

        [Fact]
        public void TakeItem_RefusedWhileHeRides_35()
        {
            var s = new LineScene(exit: false, x: 64.2);
            s.Until(Sim.Move(0), () => s.First != null && s.First.State == CarrierState.Dock);
            s.Step(Sim.Jump(0));
            s.Until(Sim.Move(0), () => s.M.Ride != null && !s.M.IsActing, 400);
            Assert.NotNull(s.M.Ride);
            Assert.False(s.M.IsActing);
            Assert.Throws<InvalidOperationException>(() => s.M.TakeItem(new TestItem { IsLight = true }));
            Assert.Equal(HoldKind.None, s.M.Hold);
        }

        [Fact]
        public void Ride_ToTheChute_TipsHimOut_TheRideIsGone_L2733()
        {
            var s = new LineScene(exit: false, x: 64.3);
            s.Until(Sim.Move(0), () => s.First != null && s.First.State == CarrierState.Dock);
            s.Step(Sim.Use());
            s.Until(Sim.Move(0), () => s.M.Ride != null, 200);
            int gone = s.Until(Sim.Move(0), () => s.M.Ride == null, 2000);
            Assert.True(gone > 0);
            Assert.Contains("Alighted:gone", s.Beats);
            Assert.False(s.M.IsActing);                                         // the scene's rule takes him from here (tipOut, L2978)
        }

        // ---- The belt's carry and its crates in the lane (L3439, L1998–L2006, L1733) ----------------------------------

        [Fact]
        public void Belt_CarriesHimBackWhileHeStandsOrWalks_ItsCratesAreGround_L3439_L2006_L1733()
        {
            var trigger = new TestSource("dl08.pawl") { Engaged = true };
            var belt = new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt());
            var g = Mech.Graph("cage", trigger, belt);                             // running from the cage checkpoint
            var lane = new TestLane(Floor(80, 100, 1.6))
                .Surface((x, y, h) => belt.SurfaceAt(x, h)).Carry((x, y) => belt.CarryVelocity(x));
            var m = new D17Motor(MotorConfig.Prototype(), lane);
            m.Place(94.0, 1.6);
            void Step(MotorInput i) { m.Step(i, Dt); g.Step(Dt, PlayerPose.Of(m)); }
            for (int i = 0; i < 60; i++) Step(Sim.Move(0));
            Assert.Equal(94.0 - 0.32, m.X, 9);                                   // −0.32 m/s standing
            double x = m.X;
            var walk = new MotorInput { Move = 1, RunModifierHeld = true };                // a walk (auto-run inverted)
            for (int i = 0; i < 120; i++) Step(walk);
            Assert.InRange(m.X - x, 0.9 * 2 - 0.32 * 2 - 0.15, 0.9 * 2 - 0.32 * 2);   // walking (after his acceleration) less the belt
            Assert.Equal(0, lane.CarryAt(90.0, 1.6));                            // off the belt
            Mech.RunUntil(g, () => belt.Count > 0 && belt.At(0).State == CrateState.Belt, 600, new PlayerPose(89.5, 1.6));
            var c = belt.At(0);
            Assert.Equal(1.6 + c.Height, lane.SurfaceAt(c.X, 1.6), 12);          // a crate on the belt is solid ground
        }

        // ---- DL-18: the strap's hop and the leaves in the lane ---------------------------------------------------------

        [Fact]
        public void Dl18_TheStrap_TugThenAHopClear_TheBenchComesDown_AndIsASeatInTheLane_DL18_3()
        {
            var bed = new FoldingLeaf("dl18.bed", FoldingLeafParams.Dl18Bed());
            var bench = new FoldingLeaf("dl18.bench", FoldingLeafParams.Dl18Bench());
            var g = new MechanismGraph();
            g.Add(bed); g.Add(bench); g.Build();
            g.Reset(new Checkpoint(FoldingTests.Ch2, "ring_a"));
            Mech.PlayAct(g, bed);                                                 // fold the bed away first
            Mech.RunUntil(g, () => bed.State == FoldingLeafState.Folded, 300);
            var lane = new TestLane(Floor(350, 356, 0)).Swept(bed, bed).Swept(bench, bench);
            var r = new InteractionResolver();
            r.Register(bench);
            var m = new D17Motor(MotorConfig.Prototype(), lane, r);
            m.Place(353.4, 0);
            Assert.Equal(0, lane.SurfaceAt(353.8, 0));                            // folded: nothing in his slab
            void Step(MotorInput i) { m.Step(i, Dt); g.Step(Dt, PlayerPose.Of(m)); }
            Step(Sim.Use());
            bool waited = false, hopped = false;
            for (int i = 0; i < 600 && m.IsActing; i++)
            {
                Step(Sim.Move(0));
                waited |= bench.State == FoldingLeafState.Waiting;                // it meets him and waits (it never crushes)
                hopped |= m.ActPhase == ActPhase.Hop;
            }
            Assert.True(waited);
            Assert.True(hopped);
            Assert.Equal(353.45 - 0.4, m.X, 9);                                   // 0.4 m back to the left (§3)
            Assert.Equal(0, m.Y, 9);
            for (int i = 0; i < 120 && bench.State != FoldingLeafState.Down; i++) Step(Sim.Move(0));
            Assert.Equal(FoldingLeafState.Down, bench.State);
            Assert.Equal(0.6, lane.SurfaceAt(353.8, 0), 9);                       // a seat at 0.6 in the lane
            Assert.Equal(0, lane.SurfaceAt(354.3, 0), 9);
            // And he can climb onto it (0.6: a mantle).
            int up = 0;
            for (; up < 400 && !(m.Y > 0.59 && !m.IsMantling); up++) Step(up % 20 == 0 ? Sim.Jump(1) : Sim.Move(1));
            Assert.Equal(0.6, m.Y, 9);
        }

        [Fact]
        public void SweptVolumeLane_AMovingLeafIsACeilingNotGround()
        {
            var bed = new FoldingLeaf("dl18.bed", FoldingLeafParams.Dl18Bed());
            var bench = new FoldingLeaf("dl18.bench", FoldingLeafParams.Dl18Bench());
            var g = new MechanismGraph();
            g.Add(bed); g.Add(bench); g.Build();
            g.Reset(new Checkpoint(FoldingTests.Ch2, "ring_a"));
            var lane = new TestLane(Floor(350, 356, 0)).Swept(bed, bed).Swept(bench, bench);
            Assert.Equal(0.7, lane.SurfaceAt(353.5, 0), 9);                       // the bed down: the quilt heaped to 0.7
            Assert.Equal(0.45, lane.SurfaceAt(352.5, 0), 9);
            Mech.PlayAct(g, bench);                                               // the bench comes down onto the quilt: propped
            Mech.RunUntil(g, () => bench.State == FoldingLeafState.Propped, 300);
            Assert.Equal(0.7, lane.SurfaceAt(353.8, 0.7), 9);                     // not ground: he slides off it
            Assert.Equal(0, lane.SurfaceAt(354.1, 0), 9);
            double ceil = lane.CeilingAt(354.1, 0);                               // past the bed's foot, under the tilted leaf
            Assert.InRange(ceil, 0.58, 0.8);                                      // its underside: he can only crouch under it
            Assert.Equal(LaneProbe.NoCeiling, lane.CeilingAt(354.3, 0));
        }

        // ---- After the mechanisms: the escort hook and #9 ride sync for lifts and carriers (MotorSync) ------------------

        private sealed class TestLift : Mechanism, ILiftRide
        {
            public TestLift() : base("t.lift") { }
            public double FloorY { get; set; }
            public double FloorVelocity => 0;
            public bool Carrying { get; set; }
            public override void Reset(in Checkpoint cp) { }
            public override void Step(in StepContext ctx) { FloorY += 0.01; }
            protected override void WriteFields(ISnapshotWriter w) { w.WriteDouble("y", FloorY); w.WriteBool("c", Carrying); }
            protected override void ReadFields(ISnapshotReader r) { FloorY = r.ReadDouble("y"); Carrying = r.ReadBool("c"); }
        }

        private sealed class TestEscort : Mechanism, IEscort
        {
            public TestEscort() : base("t.escort") { }
            public bool Want;
            public int SawEscorted;
            public bool WantsEscort => Want;
            public EscortWalk Walk => new EscortWalk(0.1, 0.8, 1.0, 1.01, -1, +1);
            public override void Reset(in Checkpoint cp) { }
            public override void Step(in StepContext ctx) { if (ctx.Player.Escorted) SawEscorted++; }
            protected override void WriteFields(ISnapshotWriter w) { }
            protected override void ReadFields(ISnapshotReader r) { }
        }

        /// <summary>A scene simulator's step reduced to the motor's part: #4 motor, #6 mechanisms, then <see cref="MotorSync"/>.</summary>
        private sealed class Pipeline
        {
            public readonly TestLift Lift = new TestLift();
            public readonly TestEscort Escort = new TestEscort();
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly D17Motor M;
            public readonly MotorSync Sync;

            public Pipeline()
            {
                G.Add(Lift); G.Add(Escort); G.Build();
                G.Reset(new Checkpoint(Checkpoint.PrototypeOrder, "start"));
                Sync = new MotorSync(G);
                M = Sim.Make(Floor(0, 10, 0), 3.0);
            }

            public void Step(MotorInput i)
            {
                M.Step(i, Dt);
                G.Step(Dt, PlayerPose.Of(M));
                Sync.AfterMechanisms(M);
            }
        }

        [Fact]
        public void MotorSync_CollectsTheGraphsEscortsAndLifts()
        {
            var p = new Pipeline();
            Assert.Same(p.Lift, Assert.Single(p.Sync.Lifts));
            Assert.Same(p.Escort, Assert.Single(p.Sync.Escorts));
        }

        [Fact]
        public void MotorSync_RideSync_PlacesHimOnACarryingLiftsFloorAfterTheMechanisms_Step9_L2959()
        {
            var p = new Pipeline();
            p.Lift.FloorY = 0.5;
            p.Step(Sim.Move(0));
            Assert.Equal(0, p.M.Y);                                               // not carrying: the lane's floor
            p.Lift.Carrying = true;
            p.Step(Sim.Move(0));
            Assert.Equal(p.Lift.FloorY, p.M.Y, 12);                               // this tick's floor (it moved at #6)
            Assert.Equal(0.52, p.M.Y, 12);
            Assert.True(p.M.Grounded);
        }

        [Fact]
        public void MotorSync_AnEscortThatWantsHim_StartsTheMotorsEscortedAct_AfterTheMechanisms_L6399()
        {
            var p = new Pipeline();
            p.Escort.Want = true;
            p.Step(Sim.Move(1));
            Assert.True(p.M.IsEscorted);                                          // started after #6, this step
            Assert.Equal(0, p.Escort.SawEscorted);
            p.Step(Sim.Move(1));
            Assert.Equal(1, p.Escort.SawEscorted);                               // the pose says so from the next step
            Assert.True(PlayerPose.Of(p.M).Escorted);
            p.Escort.Want = false;
            int home = 0;
            while (p.M.IsEscorted && home++ < 600) p.Step(Sim.Move(1));
            Assert.InRange(p.M.X, 1.0, 1.01);
            Assert.Equal(+1, p.M.Facing);
        }

        [Fact]
        public void MotorEvents_TheStuckActAsksForTheRespawnAt2s_TheDeathActAtItsCut()
        {
            var m = Sim.Make(Floor(0, 10, 0), 3.0);
            m.BeginStuck();
            double delay = double.NaN;
            int due = -1;
            for (int k = 1; k <= 200 && due < 0; k++) { m.Step(Sim.Move(1), Dt); if (m.RespawnDue(out delay)) due = k; }
            Assert.Equal(121, due);                                                // T > 2.0 s (L4521)
            Assert.Equal(1.3, delay, 12);                                          // the fade (L2997–L2999)
            m.Place(3.0, 0);
            m.Die(DeathKind.Crush);
            Assert.True(m.Shake() > 0);                                            // the death's shake, reported with the next step too
            m.Step(Sim.Move(0), Dt);
            Assert.True(m.Has(MotorEventKind.Death, "Crush"));
            for (int k = 0; k < 600 && !m.RespawnDue(out delay); k++) m.Step(Sim.Move(0), Dt);
            Assert.Equal(m.Config.DeathCut, delay, 12);
        }
    }
}
