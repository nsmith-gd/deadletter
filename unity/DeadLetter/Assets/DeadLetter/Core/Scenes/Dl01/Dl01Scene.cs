using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Dl01
{
    /// <summary>
    /// DL-01 The Wake (port_architecture §5; docs/scenes/DL-01_the_wake.md): the relay, the latch and the shutter, the
    /// cart into the trench, the crank and the door, then the passage to DL-02. Lines are index.html at 7b3c123.
    /// </summary>
    public static class Dl01Scene
    {
        public const string Id = "DL-01";

        /// <summary><c>PIT.x1</c> (L283) + 0.2: past the trench is the <c>hall</c> checkpoint (L2065).</summary>
        public const double HallX = Dl01Lane.PitX1 + 0.2;
        /// <summary><c>HALL_X</c> + 0.2 (L297, L2066): the <c>hall</c> music cue.</summary>
        public const double HallCueX = 7.3 + 0.2;
        /// <summary><c>DOOR</c> (L300): through the open door (x0 + 0.15 &lt; x &lt; x1 − 0.15) the passage starts (L2040).</summary>
        public const double DoorX0 = 10.0, DoorX1 = 10.8;
        /// <summary><c>EMERGE_X</c>, <c>PASSAGE_Z</c> (L319); the walk is <c>WALK · 0.85</c> (L2138).</summary>
        public const double EmergeX = 13.2, PassageZ = 1.25, TransitSpeed = 0.9 * 0.85;
        /// <summary><c>OPENING_FRAMES</c> (L269) at <c>FPS</c> 24.</summary>
        public const double OpeningFrames = 480;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Wake",
            // Region 1 (§0.3), all of it DL-01's (sceneName, L8137): from the depot's wall to where the passage comes out,
            // EMERGE_X, where the transit switches to region 2. Its checkpoints: start, shutter, hall, door (L7976–L7979).
            X0 = Dl01Lane.Left, X1 = EmergeX,
            Region = Dl01Lane.Region,
            // Step order = the prototype's: the relay (#5, L8511), updateMechanisms (#6: the shutter; the latch releases
            // and the crank turns inside updatePlayer, L1870–L1890), then updateCh1 (#7: the cart falls, L4756).
            Mechanisms = new[]
            {
                new MechanismDef("dl01.relay", () => new PulseSequencer("dl01.relay", PulseParams.Dl01Relay())),
                new MechanismDef("dl01.latch", () => new Latch("dl01.latch", LatchParams.Dl01Latch())),
                new MechanismDef("dl01.shutter", () => new Door("dl01.shutter", DoorParams.Dl01Shutter())),
                new MechanismDef("dl01.crank", () => new CrankActuator("dl01.crank", CrankParams.Dl01Crank())),
                new MechanismDef("dl01.door", () => new Door("dl01.door", DoorParams.Dl01Door())),
                new MechanismDef("dl01.cart", () => new TippingBridge("dl01.cart", TippingBridgeParams.Dl01Cart())),
            },
            Lane = Dl01Lane.Table,
            LaneContributors = Dl01Lane.Contributors,
            Rules = () => new Dl01Rules(),
        };

        /// <summary>The passage behind the wall (<c>TRANSIT</c>, L2131–L2136), Unity z.</summary>
        public static TransitLeg[] TransitLegs() => new[]
        {
            new TransitLeg(Math.PI, (DoorX0 + DoorX1) / 2, PassageZ),                   // away from the camera, into the doorway
            new TransitLeg(Math.PI / 2, EmergeX, PassageZ),                             // right, along the passage
            new TransitLeg(0, EmergeX, 0),                                              // back out through the second doorway
            TransitLeg.TurnTo(Math.PI / 2),                                             // and on along the lane
        };
    }

    /// <summary>
    /// DL-01's bespoke rules: the label beat when play starts (<c>startPlay</c>, L8104–L8110), the checkpoints (L1677,
    /// L2065, L1890), the crank's wait to turn back and Proud (L1890–L1893), the trench (the motor's stuck act,
    /// L4764–L4766, L4519–L4523) and the passage into DL-02 (L2040–L2042, L2129–L2157).
    /// </summary>
    public sealed class Dl01Rules : SceneRules
    {
        /// <summary>The flinch after the latch: <c>actions.Flinch.time &gt;= 1.6</c>, L1876. The latch chains it to its Pull (#22, <c>LatchParams.FlinchSeconds</c>).</summary>
        public const double FlinchSeconds = 1.6;
        /// <summary>CheckLabel at the handover: cancellable by a move after 2.5 s, held 3.2 s after the clip (L8108).</summary>
        public const double LabelCancelAfter = 2.5, LabelHold = 3.2;

        /// <summary>The label beat's seen moment (<c>seen.has('labelWake')</c>, L8107): saved, so no replay or continue plays it again.</summary>
        public const string LabelWake = "labelWake";

        public static readonly CueId VoiceDispatchItem = CueId.Of("voice:dispatch_item"), MusicHall = CueId.Of("music:hall"),
            MusicThreshold = CueId.Of("music:threshold");

        private CrankActuator _crank;
        private PulseSequencer _relay;
        private bool _heardHall;                                                                   // per life: resetWorld, L8090

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _crank = sim.Graph.Get<CrankActuator>("dl01.crank");
            _relay = sim.Graph.Get<PulseSequencer>("dl01.relay");
            _heardHall = checkpoint != "start" && checkpoint != "shutter";                         // L8090
        }

        public override void OnOpeningEnd(ChapterSim sim)
        {
            // The step that ends the opening is the first of play (f >= OPENING_FRAMES → startPlay, then updatePlayer and
            // the relay in the same step, L8506–L8516): the relay's clock reaches 480 on it.
            _relay.SetClock(Dl01Scene.OpeningFrames - 24 * ChapterSim.StepSeconds);
            if (sim.Checkpoints.Current.Name == "start" && !sim.Checkpoints.HasSeen(LabelWake))      // L8107
            {
                sim.Checkpoints.MarkSeen(LabelWake);                                                  // L8108
                // A scene act (#28): the motor's quirk counts the step it starts on in its own time (cancelAfter, the hold),
                // where the prototype compares the game clock with the clock at the start, so it ends two steps early (#2167).
                sim.StartAct(new QuirkAct(ClipNames.CheckLabel, QuirkAct.ClipSeconds(ClipNames.CheckLabel), cancel: false, startClock: sim.Clock,
                    cancelAfter: LabelCancelAfter, holdFor: LabelHold, startsThisStep: true));
                sim.Cue(VoiceDispatchItem);                                                           // L8109
            }
        }

        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            if (!freeStep || sim.Region != Dl01Lane.Region) return;
            var m = sim.Motor;
            if (_crank.Position >= 1 && m.X > Dl01Scene.DoorX0 + 0.15 && m.X < Dl01Scene.DoorX1 - 0.15 && m.Grounded)   // L2040
            {
                var legs = Dl01Scene.TransitLegs();
                sim.StartAct(new TransitAct(ActIds.Transit, legs, Dl01Scene.TransitSpeed, m.X, m.Y, m.Z,
                    TransitAct.FirstTurn(m.Yaw, legs[0], sim.Config.YawRate, ChapterSim.StepSeconds), sim.Config.YawRate,
                    OnTransitLeg, OnTransitEnd).ReturnToLaneFrom(2, sim.Config.StepInSpeed));                  // L4876
                return;
            }
            if (m.X > Dl01Scene.HallX && m.Y > -0.05) sim.Checkpoints.Reach("hall");                 // L2065
            if (m.X > Dl01Scene.HallCueX && !_heardHall && _crank.Position < 1) { _heardHall = true; sim.Cue(MusicHall); }   // L2066
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            if (log.Has("dl01.latch", MechanismEventKind.State, (int)LatchState.Released)) sim.Checkpoints.Reach("shutter");   // release(), L1677
            if (log.Has("dl01.crank", MechanismEventKind.State, (int)CrankState.Done))                                            // L1889–L1890
            {
                sim.Checkpoints.Reach("door");
                sim.Cue(MusicThreshold);
                sim.StartAct(new CrankDoneAct());
            }
            // In the trench with no bridge (trenchStuck, L4764–L4766): he stops, flinches, and the fade brings the respawn.
            if (sim.Act == null && log.Has("dl01.cart", MechanismEventKind.Event, (int)TippingBridgeEvent.Stranded)) sim.Motor.BeginStuck();
        }

        private static void OnTransitLeg(ChapterSim sim, int stage)
        {
            if (stage == 2) sim.SetRegion(2);                                                      // region 2: DL-02 (L2152, L8139)
        }

        private static void OnTransitEnd(ChapterSim sim)
        {
            sim.Checkpoints.Reach("room");                                                         // L2145
            sim.Motor.Place(Dl01Scene.EmergeX, 0, 1);
        }
    }

    /// <summary>
    /// After the fifth stroke (phase <c>done</c>, L1890–L1893): he stands until he has turned back from the wheel (yaw
    /// within 0.1 of ±π/2), then plays Proud, a quirk he can walk out of: the motor's, started at #4 before the motor
    /// steps, as the prototype's is inside <c>updatePlayer</c>. The wait itself is a scene act: the motor's crank act
    /// ends with the fifth stroke and has no "turn back" phase (#28).
    /// </summary>
    public sealed class CrankDoneAct : SceneAct
    {
        /// <summary>|yaw − π/2 · facing| &lt; 0.1, L1892.</summary>
        public const double TurnedBack = 0.1;

        /// <summary>Its kind (the crank) and phase.</summary>
        public static readonly ActId Crank = ActId.Of("dl01.crank"), Done = ActId.Of("Done");

        public CrankDoneAct() : base(Crank, Done) { }

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            var m = sim.Motor;
            if (Math.Abs(m.Yaw - Math.PI / 2 * m.Facing) < TurnedBack)
            {
                m.PlayQuirk(ClipNames.Proud, cancel: true);                                         // playQuirk('Proud'), L1893
                return false;
            }
            return true;
        }
    }
}
