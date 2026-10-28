using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Folding leaves (chapter2_plan §7 "Folding furniture"; DL-18 §3, §11): the type on its own. The bed and bench of
    /// DL-18 blocking each other are in <see cref="Dl18SceneTests"/>.
    /// </summary>
    public class FoldingTests
    {
        private const double Dt = Mech.Dt;
        internal static readonly string[] Ch2 = Checkpoint.GameOrder;

        private static InteractionQuery At(double x, double y = 0) => new InteractionQuery(x, y, 0, 1, true, false, HoldKind.None, null, null);

        /// <summary>A bench-like leaf on its own: hinged at 0.6, 0.45 long, folded vertical, 1.0 s each way.</summary>
        private static FoldingLeafParams Bench(bool startsDown = false) => new FoldingLeafParams
        {
            Station = new Station(standX: 0, reach: 0.3, face: +1),
            Travel = 1.0, HingeY = 0.6,
            Boxes = new[] { new LeafBox(-0.4, 0.4, 0, 0.45, -0.05, 0) },
            EdgeU = 0.45,
            StartsDown = startsDown, SolvedAfter = "terrace", SolvedDown = true,
        };

        private static MechanismGraph Graph(string cp, params IMechanism[] ms)
        {
            var g = new MechanismGraph();
            foreach (var m in ms) g.Add(m);
            g.Build();
            g.Reset(new Checkpoint(Ch2, cp));
            return g;
        }

        // ---- SweptBox -------------------------------------------------------------------------------------------------------

        [Fact]
        public void SweptBox_TouchingIsNotOverlapping_RotatedBoxesUseSeparatingAxes()
        {
            var a = SweptBox.Aligned(0, 1, 0, 1, 0, 1);
            Assert.True(SweptBox.Overlap(a, SweptBox.Aligned(0, 1, 0.5, 1.5, 0.5, 1.5), 1e-6));
            Assert.False(SweptBox.Overlap(a, SweptBox.Aligned(0, 1, 1, 2, 0, 1), 1e-6));              // touching
            Assert.False(SweptBox.Overlap(a, SweptBox.Aligned(1, 2, 0, 1, 0, 1), 1e-6));              // another stretch of lane
            double c = Math.Sqrt(0.5);
            var diamond = new SweptBox(0, 1, 1.5, 0.5, c, c, 0.5, 0.5);                                // left corner at 1.5 − 0.707
            Assert.True(SweptBox.Overlap(a, diamond, 1e-6));
            var far = new SweptBox(0, 1, 1.75, 0.5, c, c, 0.5, 0.5);                                   // left corner at 1.043: clear
            Assert.False(SweptBox.Overlap(a, far, 1e-6));
            var nearCorner = new SweptBox(0, 1, 1.2, 1.2, c, c, 0.2, 0.2);                             // AABBs overlap, the boxes do not
            Assert.False(SweptBox.Overlap(a, nearCorner, 1e-6));
        }

        // ---- One leaf -------------------------------------------------------------------------------------------------------

        [Fact]
        public void Leaf_MovesOnlyOnUse_AtTheToggleFrame_AndSwingsInItsTravelTime()
        {
            var leaf = new FoldingLeaf("t.leaf", Bench());
            var g = Graph("ring_a", leaf);
            Mech.Run(g, 120);
            Assert.Equal(FoldingLeafState.Folded, leaf.State);
            Assert.Equal(90, leaf.AngleDeg);
            int toggled = -1;
            Mech.PlayAct(g, leaf, onStep: (k, f) =>
            {
                if (toggled < 0 && Mech.Entered(g, "t.leaf", FoldingLeafState.Unfolding)) { toggled = k; Assert.InRange(f, 31, 31.4 + 1e-9); }
            });
            int n = Mech.RunUntil(g, () => leaf.State == FoldingLeafState.Down);
            int total = (int)Math.Round((39.0 - 31.0) / Mech.FramesPerStep) + n;
            Assert.InRange(total, 59, 62);                                       // 1.0 s from the toggle step
            Assert.True(leaf.Engaged);
            Assert.True(leaf.Standable);
            Assert.Equal(0, leaf.AngleDeg);
            leaf.FreeEdge(out double d, out double y);
            Assert.Equal(0.45, d, 12);
            Assert.Equal(0.6, y, 12);
            Mech.Run(g, 300);
            Assert.Equal(1, leaf.Position);                                      // counterbalanced: it stays
            Mech.PlayAct(g, leaf);
            Assert.Equal(FoldingLeafState.Folding, leaf.State);
            Mech.RunUntil(g, () => leaf.State == FoldingLeafState.Folded);
            Assert.Equal(0, leaf.Position);
        }

        [Fact]
        public void Leaf_UseMidSwing_ReversesIt()
        {
            var leaf = new FoldingLeaf("t.leaf", Bench());
            var g = Graph("ring_a", leaf);
            Mech.PlayAct(g, leaf);
            Mech.Run(g, 20);
            double p = leaf.Position;
            Assert.InRange(p, 0.4, 0.9);
            Mech.PlayAct(g, leaf);
            Assert.Equal(FoldingLeafState.Folding, leaf.State);
            Assert.True(leaf.Position < p);
        }

        [Fact]
        public void Leaf_MeetsD17_StopsWithinOneStep_Waits_AndResumesOnceHeIsClear()
        {
            var leaf = new FoldingLeaf("t.leaf", Bench());
            var g = Graph("ring_a", leaf);
            var under = Mech.Pose(0.1);                                          // standing under it
            int met = -1;
            Mech.PlayAct(g, leaf, pose: under, onStep: (k, f) =>
            {
                foreach (var e in Mech.Events(g))
                    if (e.Kind == MechanismEventKind.Event && e.Code == (int)FoldingLeafEvent.Met) { met = k; Assert.Equal(1, e.Index); }
            });
            Mech.Run(g, 30, under);
            Assert.True(met > 0);
            Assert.Equal(FoldingLeafState.Waiting, leaf.State);
            double angle = leaf.AngleDeg;
            Assert.InRange(angle, 10, 80);                                      // it stopped above his head (0.76)
            leaf.FreeEdge(out _, out double edge);
            Assert.InRange(edge, 0.76, 1.06);
            Mech.Run(g, 120, under);
            Assert.Equal(angle, leaf.AngleDeg);                                  // waits: never onto him
            Mech.Run(g, 60, Mech.Pose(0.1, crouched: true));                     // he crouches: it comes on down to his head again
            Assert.Equal(FoldingLeafState.Waiting, leaf.State);
            Assert.True(leaf.AngleDeg < angle);
            Mech.Run(g, 1, Mech.Pose(1.0));                                      // he steps clear
            Assert.Equal(FoldingLeafState.Unfolding, leaf.State);
            Mech.RunUntil(g, () => leaf.State == FoldingLeafState.Down);
            Assert.Equal(1, leaf.Position);
        }

        [Fact]
        public void Leaf_SomeoneStandingOnIt_IsNeverLifted()
        {
            var leaf = new FoldingLeaf("t.leaf", Bench(startsDown: true));
            var g = Graph("ring_a", leaf);
            var on = Mech.Pose(0.0, 0.6);                                        // standing on the seat
            Mech.PlayAct(g, leaf, pose: on);
            Mech.Run(g, 60, on);
            Assert.Equal(FoldingLeafState.Waiting, leaf.State);
            Assert.InRange(leaf.Position, 1 - 1e-5, 1);
            Mech.Run(g, 1, Mech.Pose(1.0));
            Mech.RunUntil(g, () => leaf.State == FoldingLeafState.Folded);
        }

        [Theory]
        [InlineData("ring_a", false, FoldingLeafState.Folded)]
        [InlineData("ring_a", true, FoldingLeafState.Down)]
        [InlineData("terrace", false, FoldingLeafState.Down)]                  // solved leaves persist
        public void Leaf_ResetFromCheckpoint(string cp, bool startsDown, FoldingLeafState state)
        {
            var leaf = new FoldingLeaf("t.leaf", Bench(startsDown));
            var g = Graph(cp, leaf);
            Assert.Equal(state, leaf.State);
            Assert.Equal(state == FoldingLeafState.Down ? 1 : 0, leaf.Position);
            Mech.PlayAct(g, leaf, max: 30);                                      // mid-act, then reset
            g.Reset(new Checkpoint(Ch2, cp));
            Mech.Run(g, 60);
            Assert.Equal(state, leaf.State);
        }

        [Fact]
        public void Leaf_StationAnswersFromItsFloor()
        {
            var leaf = new FoldingLeaf("t.leaf", Bench());
            Assert.True(leaf.IsAvailable(At(0.29)));
            Assert.False(leaf.IsAvailable(At(0.31)));
            Assert.False(leaf.IsAvailable(At(0, 0.06)));
            Assert.Equal("Pull", leaf.Profile.Clip);
        }

        [Fact]
        public void Leaf_RestoredMidSwing_ContinuesBitIdentically()
        {
            var a = new FoldingLeaf("t.leaf", Bench());
            var ga = Graph("ring_a", a);
            Mech.PlayAct(ga, a, max: 80);                                        // toggled at f31, act still running
            var b = new FoldingLeaf("t.leaf", Bench(startsDown: true));
            var gb = Graph("terrace", b);
            gb.Restore(Mech.Snapshot(ga));
            var ta = new List<string>();
            var tb = new List<string>();
            Mech.PlayAct(ga, a, startStep: 81, onStep: (k, f) => ta.Add(Mech.Dump(ga)));
            Mech.PlayAct(gb, b, startStep: 81, onStep: (k, f) => tb.Add(Mech.Dump(gb)));
            Assert.Equal(ta, tb);
            for (int k = 0; k < 90; k++)
            {
                var pose = Mech.Pose(k < 40 ? 0.1 : 1.0);
                Mech.Run(ga, 1, pose);
                Mech.Run(gb, 1, pose);
                Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            }
            Assert.Equal(FoldingLeafState.Down, b.State);
        }

        [Fact]
        public void Leaf_ToggleFrameAndClip_FollowTheProfile()
        {
            var p = FoldingLeafParams.Dl18Bench();
            Assert.Equal("Tug", p.Profile.Clip);
            Assert.Equal(ClipTimings.TugEvents.Done, p.ToggleFrame);                           // let go at the hop (DL-18 §3 "Stepping clear")
            Assert.Equal(ClipTimings.TugEvents.Done, p.EndFrame);
        }
    }
}
