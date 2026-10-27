using System;
using System.Collections.Generic;
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
            X0 = Dl01Lane.Left, X1 = Dl01Lane.Right,                                   // region 1 (§0.3)
            Region = Dl01Lane.Region,
            Checkpoints = new[]
            {
                new CheckpointDef("start", 1.0),                                        // START_X, L302; CHECKPOINTS L7976
                new CheckpointDef("shutter", 2.9),                                      // L7977
                new CheckpointDef("hall", 8.35),                                        // L7978
                new CheckpointDef("door", 9.62),                                        // L7979
            },
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
    /// L2065, L1890), the crank's wait to turn back and Proud (L1890–L1893), the trench
    /// (L4764–L4766, L4519–L4523) and the passage into DL-02 (L2040–L2042, L2129–L2157).
    /// </summary>
    public sealed class Dl01Rules : SceneRules
    {
        /// <summary>The flinch after the latch: <c>actions.Flinch.time &gt;= 1.6</c>, L1876. The latch chains it to its Pull (#22, <c>LatchParams.FlinchSeconds</c>).</summary>
        public const double FlinchSeconds = 1.6;
        /// <summary>CheckLabel at the handover: cancellable by a move after 2.5 s, held 3.2 s after the clip (L8108).</summary>
        public const double LabelCancelAfter = 2.5, LabelHold = 3.2;

        private readonly HashSet<string> _seen = new HashSet<string>();
        private CrankActuator _crank;
        private PulseSequencer _relay;
        private bool _heardHall;

        /// <summary>Moments already played (<c>seen</c>, L1309): a checkpoint replay skips them.</summary>
        public ICollection<string> Seen => _seen;

        public override void OnBegin(SceneSim sim, string checkpoint, bool fromOpening)
        {
            _crank = sim.Graph.Get<CrankActuator>("dl01.crank");
            _relay = sim.Graph.Get<PulseSequencer>("dl01.relay");
            _heardHall = checkpoint != "start" && checkpoint != "shutter";                         // L8090
        }

        public override void OnOpeningEnd(SceneSim sim)
        {
            // The step that ends the opening is the first of play (f >= OPENING_FRAMES → startPlay, then updatePlayer and
            // the relay in the same step, L8506–L8516): the relay's clock reaches 480 on it.
            _relay.SetClock(Dl01Scene.OpeningFrames - 24 * SceneSim.StepSeconds);
            if (sim.Checkpoints.Current.Name == "start" && _seen.Add("labelWake"))                   // L8107
            {
                sim.StartAct(new QuirkAct("CheckLabel", QuirkAct.ClipSeconds("CheckLabel"), cancel: false, startClock: sim.Clock,
                    cancelAfter: LabelCancelAfter, holdFor: LabelHold, startsThisStep: true));
                sim.Cue("voice:dispatch_item");                                                       // L8109
            }
        }

        public override void AfterMotor(SceneSim sim, bool freeStep)
        {
            if (!freeStep || sim.Region != Dl01Lane.Region) return;
            var m = sim.Motor;
            if (_crank.Position >= 1 && m.X > Dl01Scene.DoorX0 + 0.15 && m.X < Dl01Scene.DoorX1 - 0.15 && m.Grounded)   // L2040
            {
                var legs = Dl01Scene.TransitLegs();
                sim.StartAct(new TransitAct("transit", legs, Dl01Scene.TransitSpeed, m.X, m.Y, m.Z,
                    TransitAct.FirstTurn(m.Yaw, legs[0], sim.Config.YawRate, SceneSim.StepSeconds), sim.Config.YawRate,
                    OnTransitLeg, OnTransitEnd).ReturnToLaneFrom(2, sim.Config.StepInSpeed));                  // L4876
                return;
            }
            if (m.X > Dl01Scene.HallX && m.Y > -0.05) sim.Checkpoints.Reach("hall");                 // L2065
            if (m.X > Dl01Scene.HallCueX && !_heardHall && _crank.Position < 1) { _heardHall = true; sim.Cue("music:hall"); }   // L2066
        }

        public override void AfterGraph(SceneSim sim)
        {
            var log = sim.Graph.Log;
            if (log.Has("dl01.latch", MechanismEventKind.State, (int)LatchState.Released)) sim.Checkpoints.Reach("shutter");   // release(), L1677
            if (log.Has("dl01.crank", MechanismEventKind.State, (int)CrankState.Done))                                            // L1889–L1890
            {
                sim.Checkpoints.Reach("door");
                sim.Cue("music:threshold");
                sim.StartAct(new CrankDoneAct());
            }
            if (sim.Act == null && log.Has("dl01.cart", MechanismEventKind.Event, (int)TippingBridgeEvent.Stranded))             // L4764
                sim.StartAct(new TrenchStuckAct(sim.X, sim.Y, sim.Z, sim.Yaw));
        }

        private static void OnTransitLeg(SceneSim sim, int stage)
        {
            if (stage == 2) { sim.SetRegion(2); sim.Exit(); }                                     // region 2: DL-02 (L2152, L8139)
        }

        private static void OnTransitEnd(SceneSim sim)
        {
            sim.Checkpoints.Reach("room");                                                         // L2145
            sim.Motor.Place(Dl01Scene.EmergeX, 0, 1);
        }
    }

    /// <summary>
    /// After the fifth stroke (phase <c>done</c>, L1890–L1893): he stands until he has turned back from the wheel (yaw
    /// within 0.1 of ±π/2), then plays Proud, a quirk he can walk out of.
    /// </summary>
    public sealed class CrankDoneAct : SceneAct
    {
        /// <summary>|yaw − π/2 · facing| &lt; 0.1, L1892.</summary>
        public const double TurnedBack = 0.1;

        public CrankDoneAct() : base("dl01.crank", "Done") { }

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            T += dt;
            var m = sim.Motor;
            if (Math.Abs(m.Yaw - Math.PI / 2 * m.Facing) < TurnedBack)
            {
                Next = new QuirkAct("Proud", QuirkAct.ClipSeconds("Proud"), cancel: true, startClock: sim.Clock);   // playQuirk('Proud'), L1893
                return false;
            }
            return true;
        }
    }

    /// <summary>
    /// In the trench with no bridge (<c>trenchStuck</c>, L4764–L4766, L4519–L4523): he flinches after 0.2 s and, after
    /// 2.0 s, the respawn is set for 1.3 s later (<c>respawn</c>, L2997–L2999). He does not move meanwhile.
    /// </summary>
    public sealed class TrenchStuckAct : SceneAct
    {
        private bool _requested;

        public TrenchStuckAct(double x, double y, double z, double yaw) : base("dl01.trench", "Stuck")
        {
            X = x; Y = y; Z = z; Yaw = yaw;
        }

        public override bool OwnsPose => true;

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            T += dt;
            if (T > 0.2) Phase = "Flinch";
            if (T > 2.0 && !_requested) { _requested = true; sim.RespawnAt = sim.Clock + 1.3; }
            return true;                                                                            // until the respawn
        }
    }
}
