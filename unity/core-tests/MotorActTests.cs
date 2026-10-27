using System;
using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-11b (#22): the station contract the motor and U-10's mechanisms share (a station answers the query with its pose;
    /// its profile is asked again after the step-in; a follow-up clip or a hop can be chained; it faces from either side;
    /// its reach can be centred off the stand point), the pushable's own acceleration, and the acts the motor gained:
    /// quirks (CheckLabel, Flinch), stuck, death, escorted, hide.
    /// </summary>
    public class MotorActTests
    {
        private const double Dt = Sim.Dt;

        private static D17Motor WithResolver(BoxWorld w, double x, double y, out InteractionResolver r, params IInteractable[] things)
        {
            r = new InteractionResolver();
            foreach (var t in things) r.Register(t);
            return Sim.Make(w, x, y, r);
        }

        // ---- Stations: the query-taking contract ------------------------------------------------------------------------

        [Fact]
        public void Station_ProfileIsAskedAgainOnceHeHasSteppedIn_TheClipIsTheSecondAnswer_L3305()
        {
            var lever = new TestLever { StandX = 1.0, StandZ = 0.3, ProfileAtStepIn = () => new ActProfile("LeverStuck", turnIntoSet: true) };
            var m = WithResolver(BoxWorld.Flat(), 0.8, 0, out _, lever);
            m.Step(Sim.Use(), Dt);
            Assert.Equal(1, lever.ProfileAsks);                                    // turn and crouch from the first answer
            Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.Clip, 600);
            Assert.Equal(2, lever.ProfileAsks);
            Assert.Equal("LeverStuck", m.Clip);                                    // the clip from the second
            Assert.Equal(0.3, m.Z, 9);
        }

        [Fact]
        public void Pawl_PlatformReachesTheLandingWhileHeStepsIn_ItBites_L3305()
        {
            var plat = new TestSource("dl08.platform") { Position = 0.5 };
            var pawl = new Pawl("dl08.pawl", PawlParams.Dl08Pawl());
            var g = Mech.Graph("goods", pawl, plat);
            var w = BoxWorld.Flat(80, 95);
            w.AddSolid(80, 95, 1.6);
            var m = WithResolver(w, 85.3, 1.6, out _, pawl);
            Assert.True(m.PreviewUse(out var c));
            Assert.Same(pawl, c.Target);
            Assert.Equal("LeverStuck", pawl.ProfileFor(m.Query()).Clip);          // out of the window when Use starts
            void Step(MotorInput i) { m.Step(i, Dt); g.Step(Dt, PlayerPose.Of(m)); }
            Step(Sim.Use());
            plat.Position = 1.0;                                                   // up at the landing during the turn and step-in
            for (int i = 0; i < 600 && m.ActPhase != ActPhase.Clip; i++) Step(Sim.Move(0));
            Assert.Equal("LeverPull", m.Clip);
            for (int i = 0; i < 600 && m.IsActing; i++) Step(Sim.Move(0));
            Assert.True(pawl.Engaged);                                             // bit at f22
        }

        [Fact]
        public void Station_ChainsAFollowUpClip_InTheSameAct_FramesRestart_L1875()
        {
            var lever = new TestLever { StandX = 1.0, Profile = new ActProfile("Pull") };
            lever.Answer = f => f.Part == 0 ? (ClipClock.Reached(f.Frame, 10) ? ActStep.Then("Flinch", 0.06) : ActStep.Continue)
                : ActStep.DoneIf(f.Time >= 0.5 - 1e-9);
            var m = WithResolver(BoxWorld.Flat(), 1.0, 0, out _, lever);
            m.Step(Sim.Use(), Dt);
            var fades = new List<double>();
            int k = 0;
            for (; k < 600 && m.IsActing; k++)
            {
                m.Step(Sim.Move(0), Dt);
                foreach (var e in m.Events) if (e.Kind == MotorEventKind.ClipChanged && e.Name == "Flinch") fades.Add(e.Value);
            }
            Assert.Equal(new[] { 0.06 }, fades);
            var flinch = lever.Frames.FindAll(f => f.part == 1);
            Assert.Equal("Flinch", flinch[0].clip);
            Assert.Equal(0.4, flinch[0].frame, 9);                                 // its own clock from 0
            Assert.Equal(30, flinch.Count);                                        // 0.5 s
            Assert.Equal(ClipNames.Idle, m.Clip);
        }

        [Fact]
        public void Station_ChainsAHop_HeArcsBackAndLandsOnTheLane_L2884_L2894()
        {
            var lever = new TestLever { StandX = 2.0, Face = 1, Profile = new ActProfile("Tug") };
            lever.Answer = f => ClipClock.Reached(f.Frame, 10) ? ActStep.HopBy(-0.4) : ActStep.Continue;
            var w = BoxWorld.Flat();
            w.AddSolid(1.4, 1.7, 0.1);                                            // he lands on a 0.1 step
            var m = WithResolver(w, 2.0, 0, out _, lever);
            m.Step(Sim.Use(), Dt);
            double peak = 0;
            bool hop = false;
            for (int i = 0; i < 600 && m.IsActing; i++)
            {
                m.Step(Sim.Move(0), Dt);
                hop |= m.ActPhase == ActPhase.Hop && m.Clip == ClipNames.Hop;
                peak = Math.Max(peak, m.Y);
            }
            Assert.True(hop);
            Assert.InRange(peak, 0.38, 0.38 + 0.1);                                // the 0.38 arc over the climb, L2888
            Assert.Equal(1.6, m.X, 9);
            Assert.Equal(0.1, m.Y, 9);
            Assert.True(m.Grounded);
            Assert.Equal(1, m.Facing);
        }

        [Fact]
        public void Crank_FacesHimTowardItFromEitherSide_L1835()
        {
            var crank = new CrankActuator("dl01.crank", CrankParams.Dl01Crank());
            Mech.Graph("hall", crank);
            Assert.True(crank.Offer(InteractionQuery.At(9.4, 0, -1), out var left));
            Assert.Equal(+1, left.Face);
            Assert.True(crank.Offer(InteractionQuery.At(9.8, 0, +1), out var right));
            Assert.Equal(-1, right.Face);

            var m = WithResolver(BoxWorld.Flat(), 9.85, 0, out _, crank);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.Clip, 600);
            Assert.Equal(-1, m.Facing);                                            // walked to it facing −x, turned into the set
            Assert.Equal(9.62, m.X, 9);
        }

        [Fact]
        public void Brake_ReachIsThePawls_HeStandsOffItAt0_2_L5290_L5298()
        {
            var lesson = new TestSource("dl13.lesson") { Engaged = true };
            var brake = new CycleBrake("dl13.brake", CycleBrakeParams.Dl13Brake());
            Mech.Graph("lesson", lesson, brake);
            var m = WithResolver(BoxWorld.Flat(210, 230), 220.95, 0, out var r, brake);   // 0.35 past the pawl, 0.55 from the stand
            Assert.True(m.PreviewUse(out var c));
            Assert.Equal(220.4, c.StandX, 12);
            Assert.Equal(0.55, c.Distance, 9);
            Assert.False(r.Resolve(InteractionQuery.At(220.6 + 0.41), out _));
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase != ActPhase.Approach, 600);
            Assert.Equal(220.4, m.X, 9);
        }

        // ---- Pushables: their own acceleration (L2332, L4690) ------------------------------------------------------

        [Theory]
        [InlineData(1.4)]
        [InlineData(3.0)]
        [InlineData(1.3)]
        public void Push_GetsGoingAtThePushablesOwnAcceleration_L2332_L4690(double accel)
        {
            var p = new TestPushable { X = 2.0, Gap = 0.6, Speed = 0.55, Min = 2.0, Max = 10, Accel = accel };
            var m = WithResolver(BoxWorld.Flat(), 1.4, 0, out _, p);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.Hold == HoldKind.Push, 300);
            m.Step(Sim.Move(1), Dt);
            Assert.Equal(accel * Dt, m.Vx, 12);
            Sim.Run(m, Sim.Move(1), 5);
            Assert.Equal(Math.Min(0.55, accel * 6 * Dt), m.Vx, 9);
        }

        // ---- Quirks: CheckLabel, Flinch (L3841–L3856) -------------------------------------------------------------------

        [Fact]
        public void Quirk_CheckLabel_PlaysThenHolds0_8s_ARefusalWhileHolding_L3842_L3853()
        {
            var m = Sim.Make(BoxWorld.Flat());
            Assert.True(m.PlayQuirk(ClipNames.CheckLabel));
            Assert.Equal(Verb.Quirk, m.ActVerb);
            Assert.False(m.PlayQuirk(ClipNames.Proud));                            // already in an act
            int steps = Sim.RunUntil(m, Sim.Move(0), mm => !mm.IsActing, 1000);
            Assert.InRange(steps * Dt, 84 / 24.0 - 0.05 + 0.8, 84 / 24.0 - 0.05 + 0.8 + 2 * Dt);   // its clock is the mixer's, a step behind
            Assert.Equal(ClipNames.Idle, m.Clip);

            var held = Sim.Make(BoxWorld.Flat(), 0, 0, null);
            var item = new TestItem { X = 0.29 };
            var r = new InteractionResolver(); r.Register(item);
            var h = Sim.Make(BoxWorld.Flat(), 0, 0, r);
            h.Step(Sim.Use(), Dt);
            Sim.RunUntil(h, Sim.Move(0), mm => mm.Hold == HoldKind.Item, 300);
            Assert.False(h.PlayQuirk(ClipNames.CheckLabel));                       // !game.hold
            Assert.True(held.PlayQuirk(ClipNames.CheckLabel));
        }

        [Fact]
        public void Quirk_AMoveCancelsIt_OnlyPast0_3sOfTheClip_OrAfterCancelAfter_L3851_L8108()
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.PlayQuirk(ClipNames.Proud);
            Sim.Run(m, Sim.Move(1), 19);
            Assert.True(m.IsActing);                                               // 0.3 s of clip: not past it yet
            Sim.Run(m, Sim.Move(1), 1);
            Assert.False(m.IsActing);

            var k = Sim.Make(BoxWorld.Flat());
            k.PlayQuirk(ClipNames.CheckLabel, cancel: false, holdFor: 3.2, cancelAfter: 2.5);
            int cut = Sim.RunUntil(k, Sim.Move(1), mm => !mm.IsActing, 1000);
            Assert.InRange(cut * Dt, 2.5, 2.5 + 2 * Dt);
        }

        [Fact]
        public void Flinch_Is16sOfTheFlinchClip_NothingCancelsIt_L1876()
        {
            var m = Sim.Make(BoxWorld.Flat());
            Assert.True(m.Flinch());
            Assert.Equal(ClipNames.Flinch, m.Clip);
            int steps = Sim.RunUntil(m, Sim.Move(1), mm => !mm.IsActing, 300);
            Assert.Equal(97, steps);                                               // f38.4 on the mixer's clock, a step behind
        }

        // ---- Stuck and death (L4519–L4521, L7425–L7453) ----------------------------------------------------------------

        [Fact]
        public void Stuck_FlinchesFrom0_2s_AndAsksForTheRespawnAt2_0s_WithTheFade_L4520_L4521()
        {
            var m = Sim.Make(BoxWorld.Flat());
            Sim.Run(m, Sim.Move(1), 30);
            m.BeginStuck();
            m.BeginStuck();                                                        // idempotent
            Assert.Equal(0, m.Vx);
            int flinch = -1, due = -1;
            double x = m.X;
            for (int i = 1; i <= 200 && due < 0; i++)
            {
                m.Step(Sim.Jump(1), Dt);
                if (flinch < 0 && m.Clip == ClipNames.Flinch) flinch = i;
                foreach (var e in m.Events) if (e.Kind == MotorEventKind.RespawnDue) { due = i; Assert.Equal(1.3, e.Value); Assert.Equal("stuck", e.Name); }
                Assert.Equal(x, m.X);
            }
            Assert.Equal(13, flinch);
            Assert.Equal(121, due);
            Assert.Equal(Verb.Stuck, m.ActVerb);                                    // until the reload places him
        }

        [Theory]
        [InlineData(DeathKind.Crush, ClipNames.DeathCrush, 0.7, 0.9)]
        [InlineData(DeathKind.Shock, ClipNames.DeathShock, 1.0, 0.45)]
        [InlineData(DeathKind.Grabbed, ClipNames.DeathGrabbed, 1.15, 0.45)]
        [InlineData(DeathKind.Fall, ClipNames.DeathFall, 0.9, 0.7)]
        public void Death_DropsHisHold_PlaysItsClip_ThenTheCut_L7421_L7441_L7451(DeathKind how, string clip, double hold, double shake)
        {
            var item = new TestItem { X = 0.29 };
            var r = new InteractionResolver(); r.Register(item);
            var m = Sim.Make(BoxWorld.Flat(), 0, 0, r);
            item.Motor = m;
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.Hold == HoldKind.Item, 300);
            Sim.Run(m, Sim.Move(1), 20);
            double x = m.X;
            m.Die(how);
            Assert.False(item.Carried);
            Assert.Equal(x, item.X);                                               // releaseHolds: at his feet (L7429)
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.Equal(clip, m.Clip);
            Assert.Equal(MotorState.Dead, m.State);
            Assert.Contains(m.Events, e => e.Kind == MotorEventKind.Shake && e.Value == shake);
            int due = Sim.RunUntil(m, Sim.Move(1), mm => Sim.Has(mm, MotorEventKind.RespawnDue, "death"), 200);
            Assert.Equal((int)Math.Round(hold * 60), due);
            Assert.Contains(m.Events, e => e.Kind == MotorEventKind.RespawnDue && e.Value == 0.6);
            Assert.Equal(x, m.X);
        }

        // ---- Escorted (L6126–L6134) -------------------------------------------------------------------------------------

        [Fact]
        public void Escorted_HeLetsGoOfWhatHePushes_StandsThenWalksHome_L6399_L6127_L6133()
        {
            var p = new TestPushable { X = 271.6, Gap = 0.6, Min = 271.6, Max = 280 };
            var r = new InteractionResolver(); r.Register(p);
            var m = Sim.Make(BoxWorld.Flat(250, 290), 271.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.Hold == HoldKind.Push, 300);
            m.BeginEscort(new EscortWalk(0.7, 0.8, 263.45, 263.46, -1, +1));
            Assert.True(p.Released);
            Assert.False(p.Tipped);
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.True(PlayerPose.Of(m).Escorted);
            double x = m.X;
            int walk = Sim.RunUntil(m, Sim.Use(), mm => mm.X < x, 100);           // Use does nothing: he is held
            Assert.Equal(42, walk);
            Assert.Equal(-1, m.Facing);
            int home = Sim.RunUntil(m, Sim.Move(1), mm => !mm.IsActing, 1000);
            Assert.InRange(m.X, 263.45, 263.46);
            Assert.Equal(+1, m.Facing);
            Assert.InRange(home * Dt, (x - 263.46) / 0.8 - Dt, (x - 263.45) / 0.8 + Dt);
        }

        // ---- Hide (DL-14b, L6111–L6125, L5973) -----------------------------------------------------------------------------

        [Fact]
        public void Hide_BacksIntoTheNiche_Crouched_TheTrolleyPassesHim_AnyMoveBringsHimOut_L6111_L6125()
        {
            var senses = new BeingSenses { Region = 6 };
            var niche = new HideSpot("dl14b.nicheA", HideSpotParams.Dl14bNicheA());
            var trolley = new EscortTrolley("dl14b.trolley", EscortTrolleyParams.Dl14b(), senses);
            var g = Mech.Graph("corridor", niche, trolley);
            var m = WithResolver(BoxWorld.Flat(250, 290), 263.9, 0, out var r, niche);
            Assert.False(r.Resolve(InteractionQuery.At(263.7), out _));            // inset 0.15 (L5980)
            Assert.True(m.PreviewUse(out var c));
            Assert.Equal(Verb.Hide, c.Verb);
            Assert.Equal(264.05, c.StandX, 9);
            void Step(MotorInput i)
            {
                senses.BeginStep();
                m.Step(i, Dt);
                g.Step(Dt, PlayerPose.Of(m));
                if (trolley.WantsEscort && !m.IsEscorted) m.BeginEscort(trolley.Walk);
            }
            Step(Sim.Use());
            Assert.True(PlayerPose.Of(m).Hiding);
            int hidden = 0;
            for (int i = 0; i < 300 && !Sim.Has(m, MotorEventKind.ActEvent, "hidden"); i++) { Step(Sim.Move(0)); hidden = i; }
            Assert.Equal(0.62, m.Z, 9);
            Assert.True(m.Crouched);
            Assert.Equal(ClipNames.CrouchIdle, m.Clip);
            Assert.Equal(0, m.Yaw, 2);                                             // facing out
            bool passed = false;
            for (int i = 0; i < 60 * 25; i++)
            {
                Step(Sim.Move(0));
                passed |= trolley.Dir < 0 && trolley.BeamLo < m.X && trolley.BeamHi > m.X;
            }
            Assert.True(passed, "the beam swept the niche");
            Assert.NotEqual(EscortState.EscortHim, trolley.State);                // hidden: z > 0.4 (L5973)
            Assert.True(m.IsHiding);
            Step(Sim.Move(-1));
            Assert.Equal(0.62, m.Z, 9);
            int outAt = Sim.RunUntil(m, Sim.Move(0), mm => !mm.IsActing, 200);
            Assert.InRange(outAt * Dt, 0.62 / 0.7 - 2 * Dt, 0.62 / 0.7 + 2 * Dt);
            Assert.Equal(0, m.Z);
            Assert.False(m.Crouched);
        }
    
        [Fact]
        public void ActTarget_IsTheStationWhileTheActRuns_NullAfter_AndForQuirks()
        {
            var lever = new TestLever { StandX = 1.0, Profile = new ActProfile("Pull") };
            var m = WithResolver(BoxWorld.Flat(), 0.9, 0, out _, lever);
            Assert.Null(m.ActTarget);
            m.Step(Sim.Use(), Dt);
            Assert.Same(lever, m.ActTarget);
            Sim.RunUntil(m, Sim.Move(0), mm => !mm.IsActing, 600);
            Assert.Null(m.ActTarget);
            Assert.True(m.PlayQuirk(ClipNames.CheckLabel));
            Assert.Null(m.ActTarget);
        }

        // ---- The camera's view of the motor (D17Framing: the label shot L3735–L3741, the push L7788) --------------------

        [Fact]
        public void Framing_LabelShot_FromCheckLabelF2_HeldCheckEases1_1_OtherwiseNone_L3735_L3741()
        {
            var m = Sim.Make(BoxWorld.Flat(), 1.0);
            Assert.Null(D17Framing.LabelShot(m));
            Assert.True(m.PlayQuirk(ClipNames.CheckLabel, cancel: false, holdFor: 3.2, cancelAfter: 2.5));
            m.Step(Sim.Move(0), Mech.Dt);
            Assert.Null(D17Framing.LabelShot(m));                                    // f0.4: not yet
            for (int i = 0; i < 6; i++) m.Step(Sim.Move(0), Mech.Dt);
            var shot = D17Framing.LabelShot(m);
            Assert.NotNull(shot);
            Assert.Equal("label", shot.Value.Name);
            Assert.Equal(50, shot.Value.Focal);
            Assert.Equal(1.1, shot.Value.Ease);
            var l = D17Framing.EstimatedLabel(m);
            Assert.Equal(l.Y + 0.15, shot.Value.Position.Y, 12);
            Assert.Equal(CameraPush.None, D17Framing.Push(m));                       // quirks do not push in
        }
    }
}
