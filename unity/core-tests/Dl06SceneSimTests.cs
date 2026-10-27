using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-06 as Core runs it (<see cref="Dl06Scene.Def"/> in a <see cref="SceneSim"/>), for what the golden trace does not
    /// play: the world at <c>scanned</c>, the reveal's walk (stopped by DL-07's first weight; to the rail and the look over
    /// it when the weights are away), boarding only once the scan is done, the Startle when a tip bangs down near him, and
    /// the chute ride onto the heap and back to <c>scanned</c> without the reveal. L1934, L2696–L2751, L2774–L2818,
    /// L2854–L2880, L2976–L2999, L3868, L4154, L7986, L8030–L8034.
    /// </summary>
    public class Dl06SceneSimTests
    {
        private static readonly MotorInput None = MotorInput.None;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Jump = new MotorInput { JumpPressed = true, JumpHeld = true };

        private static SceneSim Begin(string cp)
        {
            var s = new SceneSim(Dl06Scene.Def()) { Clock = 200 };
            s.Begin(cp);
            return s;
        }

        /// <summary>Walks in from DL-05 (at rest in the corridor, under <c>hatch</c>) and runs on to the scanner.</summary>
        private static SceneSim WalkIn()
        {
            var s = new SceneSim(Dl06Scene.Def()) { Clock = 200 };
            s.Handover("hatch", 60.4, 0);
            Until(s, Right, x => Rules(x).Scanner.Phase == Dl06ScanPhase.Scan);
            return s;
        }

        private static ReturnToSender06 Rules(SceneSim s) => (ReturnToSender06)s.Rules;

        private static int Until(SceneSim s, MotorInput input, Func<SceneSim, bool> done, int max = 6000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " y=" + s.Y + " act=" + s.ActKind + ":" + s.ActPhase + " scan=" + Rules(s).Scanner.Phase);
        }

        // ---- The checkpoint's world -----------------------------------------------------------------------------------
        [Fact]
        public void Scanned_TheScanDone_TheBeltRunning_ToTheChute_ACarrierAtOnce_L7986_L8030_L8034()
        {
            var s = Begin("scanned");
            var r = Rules(s);
            Assert.Equal(Dl06Scene.ScannedX, s.X, 12);
            Assert.Equal(Dl06ScanPhase.Done, r.Scanner.Phase);
            Assert.Equal(30, r.Scanner.T);
            Assert.True(r.Line.Running);
            Assert.Equal(CarrierRoute.Chute, r.Line.Route);
            Assert.Equal(-18, r.StopLever.LeverDeg);
            Assert.Equal(-18, r.Points.LeverDeg);
            Assert.Equal(0, r.Line.Count);
            s.Step(None);
            Assert.Equal(1, r.Line.Count);                                                   // lastSpawn = −100, L8032
            Assert.Equal(200 + 1.0 / 60, r.Line.Clock);                                      // the game clock (the payload's seed)
            Assert.Null(s.ActKind);
        }

        // ---- The scan and the reveal ----------------------------------------------------------------------------------
        /// <summary>
        /// Under the arch the scan holds him, drawn to <c>SCANNER_X</c> (L2778, L2784); the hatch's carrier rises at 3.6 s; at
        /// 4.0 s he is free and walks on by himself at the reveal's pace (L1934, L1980) until DL-07's first weight stops him
        /// (64.6 − 0.1 − HALF, L4154); at 17.2 s he checks his label, and at its f83 the belt starts and <c>scanned</c> is his.
        /// </summary>
        [Fact]
        public void Reveal_HeWalksOnToTheRailByHimself_UntilTheFirstWeight_ThenTheLabelAndTheBelt_L1934_L2774_L2815()
        {
            var s = WalkIn();
            var r = Rules(s);
            Assert.Equal("dl06.scanner:Scan", s.ActKind + ":" + s.ActPhase);
            Until(s, None, x => r.Scanner.Phase == Dl06ScanPhase.Reveal);
            Assert.Null(s.ActKind);
            Assert.InRange(s.X, Dl06Scene.ScannerX - 0.01, Dl06Scene.ScannerX);
            Assert.Equal(1, r.Line.Count);                                                   // the hatch's carrier (L2798)
            double top = 0;
            Until(s, None, x => { top = Math.Max(top, x.Vx); return r.Scanner.Phase == Dl06ScanPhase.Check; });
            Assert.Equal(Dl06Scene.RevealWalk, top, 9);
            Assert.Equal(Dl06Lane.Weight0X - Dl06Lane.WeightR - 0.17, s.X, 2);              // against the weight
            Assert.Equal("dl06.scanner:Check", s.ActKind + ":" + s.ActPhase);
            Assert.False(r.Line.Running);
            Until(s, None, x => r.Scanner.Engaged);
            Assert.Null(s.ActKind);
            Assert.True(r.Line.Running);                                                     // startBelt, L2813
            Assert.Equal("scanned", s.Checkpoints.Current.Name);
            Assert.False(r.Peeked);
            s.Step(None);
            Assert.Equal(0, s.Motor.SlowWalkLimit);
        }

        /// <summary>With the weights out of the way he gets to the rail during the reveal and looks over it, once, uncancellable (L3868–L3870).</summary>
        [Fact]
        public void Reveal_WithTheWeightsAway_HeLooksOverTheRail_L3868()
        {
            var s = WalkIn();
            var r = Rules(s);
            foreach (var id in new[] { "dl07.weight0", "dl07.weight1" }) s.Graph.Get<CarriedItem>(id).MoveTo(ItemState.Gone, 0, 0);
            Until(s, None, x => r.Scanner.Phase == Dl06ScanPhase.Reveal);
            Until(s, None, x => x.ActKind == "quirk");
            Assert.Equal("PeekDown", s.ActPhase);
            Assert.True(s.X >= Dl06Scene.PeekX);
            Assert.True(r.Peeked);
            int n = Until(s, new MotorInput { Move = -1 }, x => x.ActKind == null, 600);     // not cancelled: it plays out
            Assert.True(n >= (QuirkAct.ClipSeconds("PeekDown") - 0.05) * 60 - 1, n.ToString());
        }

        // ---- Boarding ---------------------------------------------------------------------------------------------------
        /// <summary>Before the scan is done a standing jump beside the docked carrier is just a jump (<c>boardable()</c>, L2855).</summary>
        [Fact]
        public void Boarding_NotBeforeTheScanIsDone_L2855()
        {
            var s = WalkIn();
            var r = Rules(s);
            Until(s, None, x => r.Scanner.Phase == Dl06ScanPhase.Reveal && x.X > 64.2 && r.Line.DockLit);
            Assert.NotNull(r.Line.FindBoardable(s.X));
            s.Step(Jump);
            Assert.False(s.Motor.Grounded);
            Assert.Null(s.Motor.Ride);
            Assert.False(s.Motor.IsActing);
        }

        // ---- The tip near him -------------------------------------------------------------------------------------------
        /// <summary>On the floor past 67.8 when a tip bangs down, he starts (shake 0.25, Startle, L2735). DL-07's first weight is taken away.</summary>
        [Fact]
        public void Tip_BangsDownNearHim_HeStarts_L2735()
        {
            var s = Begin("scanned");
            s.Graph.Get<CarriedItem>("dl07.weight0").MoveTo(ItemState.Gone, 0, 0);       // out of his way (it stops him at 64.33)
            Until(s, Right, x => x.X > 68.0);
            Until(s, None, x => x.Graph.Log.Has("dl06.line", MechanismEventKind.Event, (int)CarrierLineEvent.Startle));
            Assert.Equal("quirk:Startle", s.ActKind + ":" + s.ActPhase);
            Assert.Contains("shake:0.25", s.Cues);
        }

        // ---- The chute ride ---------------------------------------------------------------------------------------------
        /// <summary>
        /// Ridden to the chute, the carrier tips him out with the post at 0.35 s (L2733): down the chute, off its foot, onto
        /// the heap (L2983–L2993); a second later the fade, 1.3 s on he is back at <c>scanned</c> (L2997–L2999, L8494), the scan
        /// done and the reveal not replayed.
        /// </summary>
        [Fact]
        public void ChuteRide_TipsHimOntoTheHeap_AndHeIsBackAtScanned_L2733_L2976_L2999()
        {
            var s = Begin("scanned");
            var r = Rules(s);
            Until(s, None, x => r.Line.DockLit);
            Until(s, Right, x => x.X > 63.6);
            Until(s, None, x => Math.Abs(x.Vx) < 1e-9);
            s.Step(Jump);
            Assert.Equal(Verb.Board, s.Motor.ActVerb);
            Until(s, None, x => x.Motor.Ride != null && !x.Motor.IsActing);
            var c = r.Line.Ride;
            Assert.NotNull(c);
            Assert.Equal(c.Position, s.X, 12);                                               // ride sync
            Until(s, None, x => x.ActKind == "dl06.chute");
            Assert.Equal(CarrierRoute.Chute, c.Route);
            Assert.Equal(CarrierState.Tip, c.State);
            Until(s, None, x => x.ActPhase == "Air");
            Assert.True(s.X >= Dl06Scene.ChuteX1 - 1e-9);
            Until(s, None, x => x.ActPhase == "Down");
            Assert.Equal(Dl06Scene.HeapHeight(s.X, -Dl06Scene.RailZ) + Dl06Scene.HeapLift, s.Y, 12);
            Assert.True(s.Y < -1);
            int fade = Until(s, None, x => x.RespawnAt > 0);
            Assert.Equal(60, fade);                                                          // a.t > 1.0
            double at = s.RespawnAt;
            Until(s, None, x => x.ActKind == null);
            Assert.True(s.Clock >= at);
            Assert.Equal(Dl06Scene.ScannedX, s.X, 12);
            Assert.Equal(0, s.Y, 12);
            Assert.Equal(Dl06ScanPhase.Done, r.Scanner.Phase);                               // the reveal is not replayed
            Assert.True(r.Line.Running);
            Assert.Null(s.Motor.Ride);
            Assert.Equal("scanned", s.Checkpoints.Current.Name);
        }
    }
}
