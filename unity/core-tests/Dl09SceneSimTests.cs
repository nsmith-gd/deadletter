using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl09;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-09 as Core runs it in the prologue's chapter (<see cref="ChapterDefs.Prologue"/>), for what the golden trace does not
    /// play: the cage slipping, catching once and held by the pawl, with him carried on its floor; riding it into the buffers
    /// (a death) and the respawn at <c>cage</c>, in DL-09, with the plates still in the tray once both were in; too light, the
    /// dip and the startle; the cable's arcs (the first touch knocks him back, the next kills him) and the respawn at
    /// <c>landing8</c>; and DL-09 begun without DL-08 (region 4 left of it is past the chapter). L3421, L4109, L4138,
    /// L4182–L4189, L4949–L4950, L5011–L5095, L7197–L7202, L7397–L7414.
    /// </summary>
    public class Dl09SceneSimTests
    {
        private static readonly MotorInput None = MotorInput.None;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };

        /// <summary>The prologue begun at <paramref name="cp"/>, both plates already in the tray if <paramref name="stowed"/>.</summary>
        private static ChapterSim Begin(string cp, bool stowed = true)
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 360 };
            if (stowed) s.Checkpoints.SetFlag(StoryFlags.CounterweightsStowed);
            s.Begin(cp);
            return s;
        }

        private static SlippingCage09 Rules(ChapterSim s) => (SlippingCage09)s.RulesOf(s.Def.Scene(Dl09Scene.Id));

        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 6000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " y=" + s.Y + " act=" + SceneSim.KindOf(s) + " scene=" + s.Current?.Id);
        }

        [Fact]
        public void BegunAtCage_HeIsInDl09OnTheUpperLanding_TheCageAtTheTop_ThePlatesInTheTray_L4109()
        {
            var s = Begin("cage");
            var r = Rules(s);
            Assert.Equal("DL-09", s.Current.Id);
            Assert.Equal((Dl09Lane.Off3 + 67.8, 3.4, 4), (s.X, s.Y, s.Region));
            Assert.Equal(SlippingCageState.Top, r.Cage.State);
            Assert.Equal(ItemState.Placed, r.Plate0.State);
            Assert.Equal(ItemState.Placed, r.Plate1.State);
            Assert.Equal(2, r.Tray.Load);
            var t = Begin("cage", stowed: false);                                               // persist.cw unset: on the landing
            Assert.Equal(ItemState.Floor, Rules(t).Plate0.State);
            Assert.Equal(Dl09Scene.PlateX[1], Rules(t).Plate1.X);
        }

        /// <summary>
        /// The full ride: in, settle, lower, shudder, slip, the catch at 1.95, the pawl thrown in the stall bites, the cage eases
        /// onto the landing and holds; Proud; he walks off onto the landing (<c>landing8</c>). The cage carries him on its floor
        /// all the way down, a step behind it (<c>game.y = c.y</c> at #4); the step the act ends, ride sync (#9) has him on it.
        /// </summary>
        [Fact]
        public void TheCageSlips_CatchesOnce_ThePawlHolds_AndRideSyncCarriesHim_L5031_L5041_L5089_L5094()
        {
            var s = Begin("cage");
            var r = Rules(s);
            Until(s, Right, x => x.Act is Dl09CageAct, 400);
            Assert.Equal(SlippingCageState.Settle, r.Cage.State);
            var phases = new List<SlippingCageState> { r.Cage.State };
            double prevCage = r.Cage.Y, minY = 9;
            int carried = 0;
            Until(s, None, x =>
            {
                if (phases[phases.Count - 1] != r.Cage.State) phases.Add(r.Cage.State);
                if (x.Act is Dl09CageAct) { Assert.Equal(prevCage, x.Y, 12); Assert.True(x.Grounded); carried++; }
                prevCage = r.Cage.Y;
                minY = Math.Min(minY, x.Y);
                return r.Cage.State == SlippingCageState.Stall;
            });
            Assert.Equal(new[] { SlippingCageState.Settle, SlippingCageState.Lower, SlippingCageState.Shudder, SlippingCageState.Slip, SlippingCageState.Stall }, phases);
            Assert.True(carried > 240);
            Assert.Equal(1.95, r.Cage.Y, 12);                                                  // caught once, 0.35 above the landing
            Assert.True(s.Checkpoints.Flags.Has(StoryFlags.CageDanger));
            for (int i = 0; i < 10; i++) s.Step(None);
            Assert.Equal(1.95, s.Y, 12);                                                       // hanging in the stall with it
            s.Step(Use);                                                                        // the pawl, in the window
            Assert.Equal(SlippingCageState.Bite, r.Cage.State);
            Assert.True(r.Pawl.Engaged);
            Until(s, None, x => !(x.Act is Dl09CageAct), 200);
            Assert.Equal(SlippingCageState.Caught, r.Cage.State);
            Assert.Equal(1.6, s.Y, 12);
            Assert.Equal("quirk:" + ClipNames.Proud, SceneSim.KindOf(s) + ":" + SceneSim.PhaseOf(s));
            Assert.False(s.Checkpoints.Flags.Has(StoryFlags.CageDanger));
            Until(s, Right, x => x.Checkpoints.Current.Name == "landing8", 400);
            Assert.Equal(1.6, s.Y, 12);
            Assert.True(s.X > Dl09Lane.ShaftX1 + 0.3);
            Assert.Equal("DL-09", s.Current.Id);
        }

        /// <summary>No pawl: the cage hits the buffers with him in it, a death (<c>die('fall')</c>, L5044); the respawn is at <c>cage</c>, in DL-09, the plates still in the tray, the cage at the top again with its pawl armed.</summary>
        [Fact]
        public void RidingItIntoTheBuffers_IsADeath_AndTheRespawnAtCage_LandsInDl09_L5042_L5044_L4109()
        {
            var s = Begin("cage");
            var r = Rules(s);
            Until(s, Right, x => x.Act is Dl09CageAct, 400);
            Until(s, None, x => x.Motor.IsDead, 600);
            Assert.Equal(SlippingCageState.Crash, r.Cage.State);
            Assert.Equal(-0.1, s.Y, 12);                                                       // on the buffers
            Assert.Equal(1, s.Deaths);
            Until(s, None, x => !x.Motor.IsDead, 400);                                          // the respawn rebuilds the world
            Assert.Equal("cage", s.Checkpoints.Current.Name);
            Assert.Equal("DL-09", s.Current.Id);
            Assert.Equal((Dl09Lane.Off3 + 67.8, 3.4), (s.X, s.Y));
            Assert.Equal(SlippingCageState.Top, r.Cage.State);
            Assert.Equal(CageCatchState.Armed, r.Pawl.State);
            Assert.Equal(ItemState.Placed, r.Plate0.State);
            Assert.Equal(ItemState.Placed, r.Plate1.State);
            Until(s, Right, x => x.Act is Dl09CageAct, 400);                                    // and it takes him again
            Assert.Equal(SlippingCageState.Settle, r.Cage.State);
        }

        /// <summary>Too light (no plates in the tray): it dips under him, bangs, hauls back up and he startles (L5020–L5029).</summary>
        [Fact]
        public void TooLight_ItDips_HaulsBack_AndHeStartles_L5020_L5029()
        {
            var s = Begin("cage", stowed: false);
            var r = Rules(s);
            Until(s, Right, x => x.Act is Dl09CageAct, 400);
            Assert.Equal(SlippingCageState.Dip, r.Cage.State);
            Until(s, None, x => !(x.Act is Dl09CageAct), 400);
            Assert.Equal(SlippingCageState.Top, r.Cage.State);
            Assert.True(r.Cage.NeedExit);
            Assert.Equal("quirk:" + ClipNames.Startle, SceneSim.KindOf(s) + ":" + SceneSim.PhaseOf(s));
            Assert.Equal(3.4, s.Y, 12);
        }

        /// <summary>
        /// The cable: walked into a live arc the first time ever, he is knocked back (no death; <c>persist.shockedOnce</c>); the
        /// next touch shorts him out (<c>die('shock')</c>), and he is back at <c>landing8</c> with the cage still caught there.
        /// </summary>
        [Fact]
        public void TheArcs_FirstTouchKnocksHimBack_TheNextKills_ThenLanding8_L7412_L7413_L7197()
        {
            var s = Begin("landing8");
            var r = Rules(s);
            Until(s, Right, x => x.X > r.Arc1.Params.X0 - 0.12, 400);
            Until(s, None, x => r.Arc1.State == LiveArcState.Live, 400);
            Until(s, Right, x => x.Act is Dl09KnockbackAct, 30);
            Assert.True(s.Checkpoints.Flags.Has(StoryFlags.ShockedOnce));
            Assert.Equal(0, s.Deaths);
            double hit = s.X;
            Until(s, None, x => !(x.Act is Dl09KnockbackAct), 200);
            Assert.Equal(0.9 * 2.5 * (23 * 0.4 - 23 * 24 / 2.0 / 60) / 60, hit - s.X, 9);         // 0.9 · 2.5 · (0.4 − t) for 23 steps: 0.1725
            Until(s, None, x => r.Arc1.State == LiveArcState.Live, 400);
            Until(s, Right, x => x.Motor.IsDead, 60);
            Assert.Equal(1, s.Deaths);
            Until(s, None, x => !x.Motor.IsDead, 400);
            Assert.Equal("landing8", s.Checkpoints.Current.Name);
            Assert.Equal("DL-09", s.Current.Id);
            Assert.Equal(SlippingCageState.Caught, r.Cage.State);
            Assert.Equal(0, r.Shocked);                                                        // per life
            Until(s, None, x => r.Arc1.State == LiveArcState.Live, 400);
        }

        /// <summary>The arcs keep the game clock's rhythm: arc A live 0.3–0.75 s, arc B 1.5–1.95 s of every 2.4 (ARCS8, L7321–L7324).</summary>
        [Theory]
        [InlineData(0.10, LiveArcState.Tell, LiveArcState.Quiet)]
        [InlineData(0.50, LiveArcState.Live, LiveArcState.Quiet)]
        [InlineData(1.30, LiveArcState.Quiet, LiveArcState.Tell)]
        [InlineData(1.70, LiveArcState.Quiet, LiveArcState.Live)]
        [InlineData(2.40 * 7 + 0.5, LiveArcState.Live, LiveArcState.Quiet)]
        public void TheArcs_FollowTheGameClock(double clock, LiveArcState a, LiveArcState b)
        {
            var g = Mech.Graph("start", new LiveArc("dl09.arc1", LiveArcParams.Dl09Arc1()), new LiveArc("dl09.arc2", LiveArcParams.Dl09Arc2()));
            var a1 = g.Get<LiveArc>("dl09.arc1"); var a2 = g.Get<LiveArc>("dl09.arc2");
            a1.BindClock(() => clock); a2.BindClock(() => clock);
            g.Step(Mech.Dt, Mech.Pose(100, 1.6));
            Assert.Equal((a, b), (a1.State, a2.State));
            g.Step(Mech.Dt, Mech.Pose(105.2, 1.6));
            Assert.Equal(a == LiveArcState.Live, Mech.Events(g).Exists(e => e.Id == "dl09.arc1" && e.Kind == MechanismEventKind.Event && e.Code == (int)LiveArcEvent.Touch));
        }

        /// <summary>
        /// Without DL-08 in the chapter, region 4 left of DL-09 is a scene the chapter lacks: through the residential doorway
        /// off the gallery he is past the chapter (as before DL-09 was added), not in DL-09 (<see cref="SceneDef.RegionStart"/>).
        /// </summary>
        [Fact]
        public void WithoutDl08_Region4LeftOfDl09_IsPastTheChapter()
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 290 };
            s.Begin("gallery");
            Until(s, Right, x => x.Region == 4, 2000);
            Assert.True(s.Exited);
            Assert.Null(s.Current);
            Assert.True(s.X < Dl09Lane.X0);
        }
    }
}
