using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-18 Room for One: the fold bed and the fold bench on one frame block each other through their swept volumes
    /// (docs/scenes/DL-18_room_for_one.md §3 "The two leaves", §4, §10, §11). No prototype exists.
    /// </summary>
    public class Dl18SceneTests
    {
        private const double Dt = Mech.Dt;

        private sealed class Room
        {
            public readonly FoldingLeaf Bed = new FoldingLeaf("dl18.bed", FoldingLeafParams.Dl18Bed());
            public readonly FoldingLeaf Bench = new FoldingLeaf("dl18.bench", FoldingLeafParams.Dl18Bench());
            public readonly MechanismGraph G = new MechanismGraph();

            public Room(string cp = "ring_a")
            {
                G.Add(Bed);
                G.Add(Bench);
                G.Build();
                G.Reset(new Checkpoint(FoldingTests.Ch2, cp));
            }

            /// <summary>Use a leaf (the whole act), then let it settle (it stops moving).</summary>
            public void Use(FoldingLeaf leaf, PlayerPose? pose = null)
            {
                Mech.PlayAct(G, leaf, pose: pose);
                Mech.RunUntil(G, () => !Moving(Bed) && !Moving(Bench), 600, pose);
            }

            private static bool Moving(FoldingLeaf l) => l.State == FoldingLeafState.Unfolding || l.State == FoldingLeafState.Folding;
        }

        private static InteractionQuery At(double x, double y = 0) => new InteractionQuery(x, y, 0, 1, true, false, HoldKind.None, null, null);

        [Fact]
        public void Start_BedDown_BenchFolded_TheSillOutOfReach()
        {
            var r = new Room();
            Assert.Equal(FoldingLeafState.Down, r.Bed.State);
            Assert.Equal(FoldingLeafState.Folded, r.Bench.State);
            Assert.True(r.Bed.Standable);
            Assert.Equal(2, r.Bed.VolumeCount);
            Assert.Equal(0, r.Bench.VolumeCount);                                  // folded on its frame: out of the shared space
        }

        [Fact]
        public void WrongPath_BenchPulledWithTheBedDown_StopsOnTheQuilt_TiltedAndNotStandable_Within1_5s()
        {
            var r = new Room();
            int steps = 0, met = -1, moved = -1;
            Mech.PlayAct(r.G, r.Bench, onStep: (k, f) =>
            {
                steps = k;
                if (moved < 0 && r.Bench.State == FoldingLeafState.Unfolding) moved = k;
                if (Met(r.G, "dl18.bench") == 0) met = k;
            });
            int more = Mech.RunUntil(r.G, () => r.Bench.State == FoldingLeafState.Propped);
            if (met < 0) met = steps + more;
            Assert.Equal(FoldingLeafState.Propped, r.Bench.State);
            Assert.InRange((met - moved) * Dt, 0, 1.0);                            // §10's 1.5 s, from when the tug lets it go
            Assert.InRange(r.Bench.AngleDeg, 15, 35);                              // "about 30° above level" (§3)
            r.Bench.FreeEdge(out _, out double edge);
            Assert.InRange(edge, 0.7, 0.85);                                       // "its free edge at about 0.82"
            Assert.False(r.Bench.Standable);
            Assert.Equal(FoldingLeafState.Down, r.Bed.State);
            Mech.Run(r.G, 300);
            Assert.Equal(FoldingLeafState.Propped, r.Bench.State);                 // it rests there
        }

        [Fact]
        public void WrongPath_BedPulledDownUnderTheBench_StopsAgainstIt_Propped_Within1_5s()
        {
            var r = new Room("terrace");                                           // bed folded, bench down
            int met = -1, k0 = 0;
            Mech.PlayAct(r.G, r.Bed, onStep: (k, f) => { k0 = k; if (met < 0 && Met(r.G, "dl18.bed") == 0) met = k; });
            int more = Mech.RunUntil(r.G, () => r.Bed.State == FoldingLeafState.Propped);
            if (met < 0) met = k0 + more;
            Assert.Equal(FoldingLeafState.Propped, r.Bed.State);
            Assert.InRange(met * Dt, 0, 1.5);
            Assert.InRange(r.Bed.AngleDeg, 15, 85);                                // the doc says "about 20°"; the rigid swing meets it sooner
            Assert.False(r.Bed.Standable);
            Assert.Equal(FoldingLeafState.Down, r.Bench.State);
        }

        [Fact]
        public void TheVolumesNeverOverlap_WhateverTheOrder()
        {
            var r = new Room();
            var script = new[] { r.Bench, r.Bed, r.Bench, r.Bed, r.Bed, r.Bench, r.Bed, r.Bench, r.Bench, r.Bed };
            foreach (var leaf in script)
            {
                Mech.PlayAct(r.G, leaf, onStep: (k, f) => AssertApart(r));
                for (int k = 0; k < 120; k++) { Mech.Run(r.G, 1); AssertApart(r); }
            }
        }

        private static void AssertApart(Room r)
        {
            for (int i = 0; i < r.Bed.VolumeCount; i++)
                for (int j = 0; j < r.Bench.VolumeCount; j++)
                    Assert.False(SweptBox.Overlap(r.Bed.Volume(i), r.Bench.Volume(j), 1e-4));
        }

        [Fact]
        public void Solution_FoldTheBed_PullTheBench_ItIsASeatAt0_6()
        {
            var r = new Room();
            r.Use(r.Bed);
            Assert.Equal(FoldingLeafState.Folded, r.Bed.State);
            Assert.Equal(0, r.Bed.VolumeCount);
            r.Use(r.Bench);
            Assert.Equal(FoldingLeafState.Down, r.Bench.State);
            Assert.True(r.Bench.Standable);
            r.Bench.FreeEdge(out double d, out double y);
            Assert.Equal(0.6, y, 12);                                              // floor → 0.6 → sill 1.2
            Assert.Equal(0.45, d, 12);
        }

        [Fact]
        public void NoTraps_FromEveryConfiguration_EachLeafGoesBackWithOneUse()
        {
            // Bed down/folded × bench folded/down/propped; the propped states are the wrong paths.
            var starts = new List<System.Func<Room>>
            {
                () => new Room(),                                                              // bed down, bench folded
                () => new Room("terrace"),                                                     // bed folded, bench down
                () => { var r = new Room(); r.Use(r.Bed); return r; },                          // both folded
                () => { var r = new Room(); r.Use(r.Bench); return r; },                        // bench propped on the quilt
                () => { var r = new Room("terrace"); r.Use(r.Bed); return r; },                 // bed propped on the bench
            };
            foreach (var make in starts)
            {
                foreach (bool bed in new[] { true, false })
                {
                    var r = make();
                    var leaf = bed ? r.Bed : r.Bench;
                    var before = leaf.State;
                    r.Use(leaf);
                    if (before == FoldingLeafState.Propped)
                        Assert.Equal(FoldingLeafState.Folded, leaf.State);                     // Use returns it to folded (§11)
                    else if (before == FoldingLeafState.Down)
                    {
                        // A leaf the other one rests on waits to fold until that one goes back: two Uses (§4).
                        var other = bed ? r.Bench : r.Bed;
                        if (leaf.State != FoldingLeafState.Folded)
                        {
                            Assert.Equal(FoldingLeafState.Waiting, leaf.State);
                            r.Use(other);
                        }
                        Assert.Equal(FoldingLeafState.Folded, leaf.State);
                    }
                    else Assert.True(leaf.State == FoldingLeafState.Down || leaf.State == FoldingLeafState.Propped);
                }
            }
        }

        [Fact]
        public void D17UnderTheBench_ItWaits_ThenComesDownWhenHeHopsClear()
        {
            var r = new Room();
            r.Use(r.Bed);
            var under = Mech.Pose(353.8);
            Mech.PlayAct(r.G, r.Bench, pose: under);
            Mech.Run(r.G, 60, under);
            Assert.Equal(FoldingLeafState.Waiting, r.Bench.State);
            Mech.Run(r.G, 1, Mech.Pose(353.45 - 0.4 - 0.2));                       // the 0.4 m hop back to the left, and a little more
            Mech.RunUntil(r.G, () => r.Bench.State == FoldingLeafState.Down);
            Assert.True(r.Bench.Standable);
        }

        [Fact]
        public void Stations_FootRailFromTheFloorBeyondTheBed_StrapFromTheFloorOrTheBed_L_DL18_11()
        {
            var r = new Room();
            Assert.True(r.Bed.IsAvailable(At(353.61)));
            Assert.True(r.Bed.IsAvailable(At(354.14)));
            Assert.False(r.Bed.IsAvailable(At(353.59)));
            Assert.False(r.Bed.IsAvailable(At(354.0, 0.45)));                     // not from the bed
            Assert.True(r.Bench.IsAvailable(At(353.45)));
            Assert.True(r.Bench.IsAvailable(At(353.45, 0.45)));                    // from the bed
            Assert.True(r.Bed.Offer(At(353.7), out var pose));
            Assert.Equal(-1, pose.Face);
            Assert.Equal(354.0, pose.StandX, 12);
        }

        [Theory]
        [InlineData("ring_a", FoldingLeafState.Down, FoldingLeafState.Folded)]
        [InlineData("terrace", FoldingLeafState.Folded, FoldingLeafState.Down)]
        public void ResetFromCheckpoint_SolvedLeavesPersist(string cp, FoldingLeafState bed, FoldingLeafState bench)
        {
            var r = new Room(cp);
            r.Use(r.Bench);
            r.G.Reset(new Checkpoint(FoldingTests.Ch2, cp));
            Assert.Equal(bed, r.Bed.State);
            Assert.Equal(bench, r.Bench.State);
        }

        [Fact]
        public void RestoredWhileTheBenchSwings_ContinuesBitIdentically()
        {
            var a = new Room();
            Mech.PlayAct(a.G, a.Bench);
            Mech.Run(a.G, 5);
            var b = new Room("terrace");
            b.G.Restore(Mech.Snapshot(a.G));
            for (int k = 0; k < 200; k++)
            {
                Mech.Run(a.G, 1);
                Mech.Run(b.G, 1);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
            Assert.Equal(FoldingLeafState.Propped, b.Bench.State);
        }

        private static int Met(MechanismGraph g, MechanismId id)
        {
            foreach (var e in Mech.Events(g))
                if (e.Id == id && e.Kind == MechanismEventKind.Event && e.Code == (int)FoldingLeafEvent.Met) return e.Index;
            return -1;
        }
    }
}
