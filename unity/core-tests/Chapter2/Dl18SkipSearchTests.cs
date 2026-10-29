using System;
using System.Collections.Generic;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl18;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-18: is the only way onto the sill (1.2) the solution, the bench down at 0.6 (§4)? From every place he can stand
    /// below it (the gallery and the box room floor, the space between the bed's foot and the sill, the bed's top while it is
    /// down, the seat while it is down; the bench folded or propped and the quilt are never ground), in every leaf
    /// configuration, standing, walking and running jumps in both directions, each in the real <see cref="ChapterSim"/>.
    /// <para><b>#46.</b> The motor's mid-air catch (the prototype's) reaches about 1.09 m above takeoff, so from the bed
    /// (0.45) a running jump at the sill catches it (0.75 up): §10's "Wrong path, reach" fails. Until the director rules on
    /// #46 this test asserts that skip exists, from the bed with the bench folded; the ruling flips that line to "no skip".
    /// Every other skip is asserted absent, and so is any with the bench propped: the slide-off
    /// (<see cref="Dl18SlideAct"/>) meets him first, and always leaves him on the bed.</para>
    /// </summary>
    public class Dl18SkipSearchTests
    {
        private enum Mode { Stand, Walk, Run }

        private struct Outcome
        {
            public bool Up, BadSlide;
        }

        public static IEnumerable<object[]> Configurations() => new[]
        {
            new object[] { "start" }, new object[] { "benchPropped" }, new object[] { "bothFolded" }, new object[] { "solved" }, new object[] { "bedPropped" },
        };

        /// <summary>The leaves in a configuration, played on the chapter's own graph (bed down / folded / propped; bench folded / down / propped).</summary>
        internal static ChapterSim Configure(string config)
        {
            var s = new ChapterSim(ChapterDefs.SomeoneHome());
            s.Begin(config == "solved" || config == "bedPropped" ? "terrace" : "ring_a");
            var bed = s.Graph.Get<FoldingLeaf>(Dl18Scene.Bed);
            var bench = s.Graph.Get<FoldingLeaf>(Dl18Scene.Bench);
            bool Settled(FoldingLeaf l) => l.State == FoldingLeafState.Down || l.State == FoldingLeafState.Folded || l.State == FoldingLeafState.Propped;
            void Toggle(FoldingLeaf l)
            {
                Mech.PlayAct(s.Graph, l);
                Assert.True(Mech.RunUntil(s.Graph, () => Settled(bed) && Settled(bench), 600) > 0);
            }
            if (config == "benchPropped") Toggle(bench);
            else if (config == "bothFolded" || config == "bedPropped") Toggle(bed);
            return s;
        }

        /// <summary>
        /// #46: the bed-to-sill catch is the only skip, and it still exists with the bench folded. When #46 is ruled on, flip
        /// <c>expectBedSkip</c> for "start" to false.
        /// </summary>
        [Theory]
        [MemberData(nameof(Configurations))]
        public void Issue46_TheOnlySkipIsTheBedToSillCatch_AndItStillExistsWithTheBenchFolded(string config)
        {
            var s = Configure(config);
            var snap = Mech.Snapshot(s.Graph);
            var bench = s.Graph.Get<FoldingLeaf>(Dl18Scene.Bench);
            bool benchDown = bench.State == FoldingLeafState.Down;                                 // the solution's step: up is legitimate
            bool expectBedSkip = config == "start";                                                // #46: flips to false when ruled on
            int attempts = 0, upFromBench = 0;
            var skips = new List<string>();
            foreach (double x0 in Takeoffs())
            {
                double y0 = s.Lane.SupportAt(x0);
                if (!Stands(s, bench, x0, y0) || y0 >= Dl18Lane.SillY) continue;
                string surface = Surface(x0, y0);
                foreach (int dir in new[] { 1, -1 })
                    foreach (Mode mode in new[] { Mode.Stand, Mode.Walk, Mode.Run })
                    {
                        var o = Attempt(s, snap, bench, x0, y0, dir, mode);
                        attempts++;
                        string what = config + ": " + mode + " jump " + (dir > 0 ? "right" : "left") + " from the " + surface + " at " + x0.ToString("F2");
                        Assert.False(o.BadSlide, what + ": the slide-off left him off the bed");
                        if (!o.Up) continue;
                        if (benchDown) { if (surface == "bench") upFromBench++; continue; }
                        Assert.True(surface == "bed", what + " reached the sill");                // no skip but the bed's (#46)
                        skips.Add(what);
                    }
            }
            Assert.True(attempts >= 150, config + ": " + attempts + " attempts");
            if (benchDown) Assert.True(upFromBench > 0, config + ": the search never found the bench-to-sill climb");
            if (expectBedSkip) Assert.NotEmpty(skips);                                             // #46: the catch from the bed
            else Assert.True(skips.Count == 0, config + ": " + string.Join("; ", skips));
        }

        /// <summary>The gallery every 0.25, the box room and the doorway's foot every 0.05.</summary>
        private static IEnumerable<double> Takeoffs()
        {
            for (double x = 347.3; x < Dl18Lane.RoomX0; x += 0.25) yield return x;
            for (int i = 0; i <= 52; i++) yield return Dl18Lane.RoomX0 + 0.05 * i;
        }

        private static string Surface(double x, double y)
            => y == 0 ? (x < Dl18Lane.RoomDoorX ? "gallery" : "floor") : Math.Abs(y - 0.45) < 1e-9 ? "bed" : Math.Abs(y - 0.6) < 1e-9 ? "bench" : "y" + y;

        /// <summary>He can stand at (x, y): his body clear of any face higher than a step, and not in the propped bench.</summary>
        private static bool Stands(ChapterSim s, FoldingLeaf bench, double x, double y)
        {
            var c = s.Config;
            return s.Lane.SurfaceAt(x - c.Half + 1e-6) <= y + c.StepUp && s.Lane.SurfaceAt(x + c.Half - 1e-6) <= y + c.StepUp
                && !Dl18Rules.MeetsPropped(bench, x, y, false);
        }

        private static Outcome Attempt(ChapterSim s, MemorySnapshot snap, FoldingLeaf bench, double x0, double y0, int dir, Mode mode)
        {
            s.Graph.Restore(snap);
            s.EndAct();
            s.RespawnAt = 0;
            double start = x0;
            if (mode != Mode.Stand)
            {
                start = x0 - dir * 1.0;                                                            // a run-up on the same surface,
                for (int k = 0; k < 100 && !(Math.Abs(s.Lane.SupportAt(start) - y0) < 1e-9 && Stands(s, bench, start, y0)); k++) start += dir * 0.01;
            }
            s.Motor.Place(start, y0, dir);
            var o = new Outcome();
            var hold = new MotorInput { Move = mode == Mode.Stand ? 0 : dir, RunModifierHeld = mode == Mode.Walk };
            bool sliding = false;
            if (mode != Mode.Stand)
                for (int k = 0; k < 150 && (dir > 0 ? s.X < x0 : s.X > x0) && !(k > 5 && s.Vx == 0) && !s.Busy; k++) Watch(s, hold, ref o, ref sliding);
            var jump = hold;
            jump.JumpPressed = true;
            Watch(s, jump, ref o, ref sliding);
            for (int k = 0; k < 75; k++) Watch(s, hold, ref o, ref sliding);
            for (int k = 0; k < 120; k++) Watch(s, default, ref o, ref sliding);
            return o;
        }

        private static void Watch(ChapterSim s, MotorInput input, ref Outcome o, ref bool sliding)
        {
            s.Step(input);
            if (s.Grounded && s.X >= Dl18Lane.SillX && s.Y >= Dl18Lane.SillY - 1e-9) o.Up = true;
            bool now = s.SceneActKind == Dl18SlideAct.SlideKind;
            if (sliding && !now && !(Math.Abs(s.X - Dl18SlideAct.BackX) < 1e-9 && Math.Abs(s.Y - 0.45) < 1e-9)) o.BadSlide = true;   // always ends on the bed
            sliding = now;
        }
    }
}
