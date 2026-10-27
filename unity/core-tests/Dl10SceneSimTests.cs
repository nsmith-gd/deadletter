using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl09;
using DeadLetter.Core.Scenes.Dl10;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-10 as Core runs it in the prologue's chapter (<see cref="ChapterDefs.Prologue"/>), for what the golden trace does not
    /// play: the lobby's UP with the car empty (it buzzes, the car stays, the Pips flash, he startles the first time only); the
    /// service crank cancelled by a move and resumed (the door holds where left; four strokes in all, and its wall goes at
    /// 0.98); the lift that will not leave without the suitcase on its plate and the gate shut, then the ride down to ring C's
    /// level and on into region 5; and <c>uponly</c> reached from DL-09 and respawned at, in DL-10. L2047, L3455–L3461,
    /// L4191–L4197, L4212–L4236, L4526–L4637, L4937.
    /// </summary>
    public class Dl10SceneSimTests
    {
        private static readonly MotorInput None = MotorInput.None;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Left = new MotorInput { Move = -1 };
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };

        private static ChapterSim Begin(string cp = "uponly")
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 420 };
            s.Begin(cp);
            return s;
        }

        private static UpOnly10 Rules(ChapterSim s) => (UpOnly10)s.RulesOf(s.Def.Scene(Dl10Scene.Id));

        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 6000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " y=" + s.Y + " act=" + SceneSim.KindOf(s) + ":" + SceneSim.PhaseOf(s) + " scene=" + s.Current?.Id);
        }

        /// <summary>
        /// Walks until he is past <paramref name="x"/> or at rest against a wall, then stands. Stopped by something he can
        /// climb (the suitcase on the lane, 0.2 high) he jumps it, empty-handed; a wall stops him for good.
        /// </summary>
        private static void WalkTo(ChapterSim s, double x)
        {
            var dir = x > s.X ? Right : Left;
            var hop = new MotorInput { Move = dir.Move, JumpPressed = true, JumpHeld = true };
            double last = double.NaN;
            int hops = 0, still = 0;
            for (int i = 0; i < 3000; i++)
            {
                s.Step(dir);
                bool there = dir.Move > 0 ? s.X >= x : s.X <= x;
                still = s.X == last && !s.Busy && s.Grounded ? still + 1 : 0;                       // ten steps without moving: stopped
                last = s.X;
                if (there) break;
                if (still < 10) continue;
                still = 0;
                if (s.Motor.Hold != HoldKind.None || hops++ > 0 || s.Lane.SupportAt(s.X + dir.Move * 0.25) <= s.Y + 0.05) break;
                s.Step(hop);
                Until(s, dir, t => t.Grounded && !t.Busy, 200);
                last = double.NaN;
            }
            Until(s, None, t => t.Vx == 0 && !t.Busy, 200);
        }

        /// <summary>Use, then the motor's act to its end (on <paramref name="target"/>); the lift's events meanwhile.</summary>
        private static List<MechanismEvent> UseOn(ChapterSim s, IInteractable target, int max = 1200)
        {
            var events = new List<MechanismEvent>();
            void Collect(ChapterSim t)
            {
                var log = t.Graph.Log;
                for (int i = 0; i < log.Count; i++) if (log[i].Id.Value == "dl10.lift" && log[i].Kind == MechanismEventKind.Event) events.Add(log[i]);
            }
            s.Step(Use);
            Collect(s);
            Assert.Same(target, s.MotorActTarget);
            Until(s, None, t => { Collect(t); return ReferenceEquals(t.MotorActEndedOn, target); }, max);
            return events;
        }

        private static bool Raised(ChapterSim s, CueId id)
        {
            foreach (var c in s.Cues) if (c.Id == id) return true;
            return false;
        }

        // ---- The empty car -------------------------------------------------------------------------------------------------
        /// <summary>
        /// The lobby's UP with the car empty (L4584, L4590–L4595): he turns to the wall and presses (PressButtonHigh f16), the
        /// panel buzzes, the Pips flash <c>car10</c>, and the car stays; 0.2 s after the act he startles, the first time ever
        /// (<c>once('uoBuzz')</c>). The second buzz is only a buzz.
        /// </summary>
        [Fact]
        public void TheEmptyCar_UpBuzzes_TheCarStays_AndHeStartlesTheFirstTimeOnly_L4584_L4590_L4595()
        {
            var s = Begin();
            var r = Rules(s);
            Assert.Equal("DL-10", s.Current.Id);
            WalkTo(s, Dl10Lane.UpStand);
            Assert.True(Math.Abs(s.X - Dl10Lane.UpStand) < 0.22, s.X.ToString());
            bool pips = false;
            s.Step(Use);
            Assert.Same(r.UpButton, s.MotorActTarget);
            var events = new List<RelocationLiftEvent>();
            Until(s, None, t =>
            {
                pips |= Raised(t, Dl10Scene.PipsCar10);
                if (t.Graph.Log.Has(r.Lift.Id, MechanismEventKind.Event, (int)RelocationLiftEvent.Buzz)) events.Add(RelocationLiftEvent.Buzz);
                if (t.Graph.Log.Has(r.Lift.Id, MechanismEventKind.Event, (int)RelocationLiftEvent.Go)) events.Add(RelocationLiftEvent.Go);
                return ReferenceEquals(t.MotorActEndedOn, r.UpButton);
            });
            Assert.Equal(new[] { RelocationLiftEvent.Buzz }, events);
            Assert.True(pips);
            Assert.Equal(RelocationLiftState.Idle, r.Lift.State);
            Assert.Equal(0, r.Lift.D);
            Assert.False(r.Lift.Ready);
            Assert.Equal(Dl10Lane.UpStand, s.X, 12);
            Assert.True(s.Clock - r.BuzzAt < 1.5);
            Assert.True(s.Checkpoints.HasSeen(Dl10Scene.SeenBuzz));
            int startle = Until(s, None, t => SceneSim.KindOf(t) == "quirk", 30);
            Assert.Equal(ClipNames.Startle, SceneSim.PhaseOf(s));
            Assert.InRange(startle, 11, 13);                                                        // setTimeout(…, 200)
            Until(s, None, t => !t.Busy, 200);

            s.Step(Use);                                                                            // again: a buzz, no startle
            Assert.Same(r.UpButton, s.MotorActTarget);
            double before = r.BuzzAt;
            Until(s, None, t => ReferenceEquals(t.MotorActEndedOn, r.UpButton));
            Assert.True(r.BuzzAt > before);
            for (int i = 0; i < 60; i++) { s.Step(None); Assert.Null(SceneSim.KindOf(s)); }
        }

        // ---- The crank -----------------------------------------------------------------------------------------------------
        /// <summary>
        /// The service door's crank (L4565–L4577, L4318, L4194): up to it against the shut door, he winds; a move after 0.5 s
        /// lets go and the door holds where it was left, still blocking the lane; Use again resumes from that opening, and four
        /// strokes in all wind it fully up (1.45 m), when its wall goes and he walks on to the counterweight's far wall.
        /// </summary>
        [Fact]
        public void TheCrank_OpensTheServiceDoorOverFourStrokes_AndResumesAfterACancel_L4565_L4577()
        {
            var s = Begin();
            var r = Rules(s);
            WalkTo(s, Dl10Lane.Door);
            Assert.Equal(Dl10Lane.Door - Dl10Lane.Half - 0.01, s.X, 9);                           // the shut door's wall (L4194)
            int strokes = 0;
            s.Step(Use);
            Assert.Same(r.Crank, s.MotorActTarget);
            Until(s, None, t =>
            {
                if (t.Graph.Log.Has(r.Crank.Id, MechanismEventKind.Event, (int)CrankEvent.Stroke)) strokes++;
                return r.Crank.Strokes == 2 && r.Crank.Position > 0.55;
            }, 600);
            Until(s, Left, t => !t.Busy, 10);                                                       // a move lets go (a.t > 0.5)
            double held = r.Crank.Position;
            Assert.InRange(held, 0.55, 0.75);
            for (int i = 0; i < 120; i++) s.Step(None);
            Assert.Equal(CrankState.Idle, r.Crank.State);
            Assert.Equal(held, r.Crank.Position);                                                   // it holds where left
            Assert.Equal(held * 1.45, r.ServiceDoor.Position, 12);
            WalkTo(s, Dl10Lane.Door);
            Assert.True(s.X < Dl10Lane.Door - Dl10Lane.Half);                                       // still in the way

            s.Step(Use);                                                                            // resumes: round(0.6 · 4) = 2 done
            Assert.Same(r.Crank, s.MotorActTarget);
            Until(s, None, t =>
            {
                if (t.Graph.Log.Has(r.Crank.Id, MechanismEventKind.Event, (int)CrankEvent.Stroke)) strokes++;
                return ReferenceEquals(t.MotorActEndedOn, r.Crank);
            }, 900);
            Assert.Equal(4, strokes);
            Assert.Equal(CrankState.Done, r.Crank.State);
            Assert.Equal(1, r.Crank.Position);
            Assert.Equal(1.45, r.ServiceDoor.Position, 12);
            WalkTo(s, Dl10Lane.CwX1);
            Assert.Equal(Dl10Lane.CwX1 - Dl10Lane.Half, s.X, 9);                                    // through, to the shaft's far wall (L4196)
            Assert.Equal(Dl10Lane.Deck, s.Y, 12);
        }

        // ---- The lift ------------------------------------------------------------------------------------------------------
        /// <summary>
        /// The lift will not leave without the suitcase on its plate (L4584): from the counterweight's footplate its UP buzzes and
        /// the car stays. The suitcase lifted from the lane and set into the car (SetDown in its doorway, L4543–L4561): the plate
        /// feels it, the gate draws shut over 0.8 + 1.4 s and only then is it ready; UP from the footplate sends the car up for
        /// good and he rides the counterweight down (a step behind it, L4600), the <c>ringc</c> moment and its cold light, let go
        /// at 22 s on ring C's level; he walks on into region 5 past <c>REGION5_X</c> (L2047), out of the chapter.
        /// </summary>
        [Fact]
        public void TheLiftWontLeave_WithoutTheCaseOnThePlate_ThenHeRidesTheCounterweightDown_L4584_L4600_L2047()
        {
            var s = Begin();
            var r = Rules(s);
            WalkTo(s, Dl10Lane.Door);
            s.Step(Use);
            Until(s, None, t => ReferenceEquals(t.MotorActEndedOn, r.Crank), 900);
            WalkTo(s, Dl10Lane.CwStand);
            Assert.True(s.X > Dl10Lane.CwX0 + 0.1 && s.X < Dl10Lane.CwX1);
            var ev = UseOn(s, r.ServiceUp);                                                         // empty: it buzzes
            Assert.Single(ev);
            Assert.Equal((int)RelocationLiftEvent.Buzz, ev[0].Code);
            Assert.Equal(0, ev[0].Index);
            Assert.Equal(RelocationLiftState.Idle, r.Lift.State);
            Assert.Null(s.Act);
            Assert.Equal(Dl10Lane.Deck, s.Y, 12);
            Until(s, None, t => !t.Busy, 200);                                                      // (the first buzz's startle)

            WalkTo(s, Dl10Lane.CaseX + 0.35);                                                       // back for the suitcase
            UseOn(s, r.Case);
            Assert.Equal(HoldKind.Item, s.Motor.Hold);
            Assert.Equal(ItemState.Carried, r.Case.State);
            WalkTo(s, Dl10Lane.CarX0 + 0.1);
            UseOn(s, s.Motor.PreviewUse(out var c) ? c.Target : null);                             // into the car's doorway
            Assert.Equal(HoldKind.None, s.Motor.Hold);
            Assert.Equal(ItemState.Placed, r.Case.State);
            Assert.Equal(Dl10Lane.CarMid, s.X, 12);
            Assert.Equal(0, s.Z, 12);                                                               // stepped back out
            Assert.Equal(1, r.CarPlate.Load);
            Until(s, None, t => r.Lift.Ready, 200);
            Assert.Equal(DoorState.Open, r.CarGate.State);

            WalkTo(s, Dl10Lane.CwStand);
            s.Step(Use);
            Assert.Same(r.ServiceUp, s.MotorActTarget);
            Until(s, None, t => t.Act is Dl10RideAct, 200);
            Assert.True(r.Lift.Riding);
            Assert.Equal(PrologueMoments.RingC, r.Moment.Current);
            double prev = r.Lift.CounterweightY;
            int rode = 0;
            Until(s, None, t =>
            {
                if (t.Act is Dl10RideAct) { Assert.Equal(prev, t.Y, 12); Assert.Equal(Dl10Lane.CwStand, t.X); Assert.True(t.Grounded); rode++; }
                prev = r.Lift.CounterweightY;
                return !(t.Act is Dl10RideAct);
            }, 2000);
            Assert.InRange(rode, 1270, 1330);                                                       // from f34 to 22 s on the cue
            Assert.Equal(RelocationLiftState.Gone, r.Lift.State);
            Assert.Equal(0, s.Y, 12);
            Assert.True(r.LightOff >= 22 && r.LightOff < 22 + 1.0 / 30, r.LightOff.ToString());
            Assert.Equal(0, r.ColdLight(s.Clock + 1.5));                                            // off over 1.5 s from there
            Assert.Equal("DL-10", s.Current.Id);
            Until(s, Right, t => t.Exited, 200);
            Assert.Equal(5, s.Region);
            Assert.True(s.X > Dl10Lane.X1);
            Assert.Equal(0, s.Y, 12);
        }

        // ---- Checkpoints ---------------------------------------------------------------------------------------------------
        /// <summary>
        /// <c>uponly</c> is reached walking in from DL-09's balcony, grounded past <c>UPONLY.x0 + 0.4</c> (L4937); a respawn there
        /// lands in DL-10 (x 119.4 on the deck, region 4) with the lobby as the checkpoint left it: the suitcase back on the
        /// lane, the car empty at the deck, the service door down (§9).
        /// </summary>
        [Fact]
        public void Uponly_IsReachedFromDl09_AndARespawnThereLandsInDl10_L4937()
        {
            var s = Begin("tunnel");
            foreach (var seen in new[] { Dl09Scene.SeenHopscotch, Dl09Scene.SeenAwe, Dl09Scene.SeenLabel }) s.Checkpoints.MarkSeen(seen);
            var r = Rules(s);
            Assert.Equal("DL-09", s.Current.Id);
            Until(s, Right, t => t.Checkpoints.Current.Name == Dl10Scene.UpOnlyCheckpoint, 3000);
            Assert.True(s.X > Dl10Scene.UpOnlyFrom);
            Assert.Equal("DL-10", s.Current.Id);

            WalkTo(s, Dl10Lane.CaseX + 0.35);                                                       // play on: the suitcase lifted,
            UseOn(s, r.Case);
            WalkTo(s, Dl10Lane.CarX0 + 0.1);
            UseOn(s, s.Motor.PreviewUse(out var c) ? c.Target : null);                             // into the car,
            Until(s, None, t => r.Lift.Ready, 200);
            Assert.Equal(1, r.CarPlate.Load);

            s.Respawn();                                                                            // and back at uponly
            Assert.Equal("DL-10", s.Current.Id);
            Assert.Equal((Dl10Lane.X0 + 0.6, Dl10Lane.Deck, 4), (s.X, s.Y, s.Region));
            Assert.Equal(4, s.Lane.Region);
            Assert.Equal(HoldKind.None, s.Motor.Hold);
            Assert.Equal(ItemState.Floor, r.Case.State);
            Assert.Equal(Dl10Lane.CaseX, r.Case.X);
            Assert.Equal(0, r.CarPlate.Load);
            Assert.Equal(DoorState.Closed, r.CarGate.State);
            Assert.Equal(RelocationLiftState.Idle, r.Lift.State);
            Assert.Equal(0, r.Crank.Position);
            Assert.Null(r.Moment.Current);
            for (int i = 0; i < 60; i++) s.Step(None);
            Assert.Equal("DL-10", s.Current.Id);
            Assert.Equal(Dl10Lane.Deck, s.Y, 12);

            var store = new MemorySaveStore();                                                      // continued from a slot at uponly: the same
            store.Save(0, new SaveModel { Checkpoint = Dl10Scene.UpOnlyCheckpoint, Scene = ChapterDefs.PrologueId });
            var t2 = new ChapterSim(ChapterDefs.Prologue(), store: store);
            Assert.True(t2.Continue());
            Assert.Equal("DL-10", t2.Current.Id);
            Assert.Equal((Dl10Lane.X0 + 0.6, Dl10Lane.Deck, 4), (t2.X, t2.Y, t2.Region));
        }
    }
}
