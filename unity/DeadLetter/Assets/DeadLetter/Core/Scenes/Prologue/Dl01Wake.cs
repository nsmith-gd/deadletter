using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Prologue
{
    /// <summary>
    /// DL-01 The Wake (port_architecture §5 row; docs/scenes/DL-01_the_wake.md). Region 1, lane x −0.3 → 11.45.
    /// He wakes in the cradle at 1.0, crouches under the fallen shutter to pull its latch (3.0), hops the fallen
    /// conveyor (3.6–4.4, 0.22), pushes the depot cart into the drain trench (6.6–8.0, −0.8) to bridge it, cranks the
    /// bulkhead door (9.62, five strokes) and walks out through it (10.15–10.65) into the passage to DL-02.
    /// When the opening hands over he checks his label (<c>labelWake</c>: CheckLabel held 3.2 s, the label shot, the
    /// <c>dispatch_item</c> voice; once per game, L8105–L8109); walking into the trench with no bridge he is stuck and
    /// respawns (L4764–L4766). Values are index.html at 7b3c123, cited per line. Not ported here (no Core system yet): the
    /// cord lamp and the curios' acts (cord, scale <c>WeighSelf</c>, dispatch <c>ReadRoute</c>), the crank's Proud quirk
    /// (L1895), hints and glints, the tannoy, lights; the passage transit belongs to the DL-01 → DL-02 seam (§7).
    /// </summary>
    public sealed class Dl01Wake : SceneDefinition
    {
        public const string SceneId = "DL-01";

        public static readonly MechanismId RelayId = "dl01.relay", LatchId = "dl01.latch", ShutterId = "dl01.shutter",
            CrankId = "dl01.crank", DoorId = "dl01.door", CartId = "dl01.cart", ScaleId = "dl01.scale";

        // ---- Lane (index.html) --------------------------------------------------------------------------------------
        public const double LeftLimit = -0.3, RightLimit = 11.45, LockedLimit = 3.02;              // L303
        public const double StepX0 = 3.6, StepX1 = 4.4, StepH = 0.22;                               // STEP, the first hop, L281
        public const double PitX0 = 6.6, PitX1 = 8.0, PitY = -0.8;                                  // PIT, L283
        public const double CeilingSplitX = 2.6, CeilingLow = 2.45, CeilingHigh = 4.0;              // ceilingAt, L1632
        public const double ShutterPivotX = 0.2, ShutterPivotY = 1.6;                               // SHUTTER_PIVOT, L276
        /// <summary><c>SHUTTER_PATH</c>, L275: the shutter's underside, closed.</summary>
        public static readonly double[] ShutterPath = { 0.2, 1.6, 2.0, 0.62, 3.2, 0.6, 3.4, 0.02 };
        public const double HallX = 7.3;                                                            // HALL_X, L299
        public const double DoorX0 = 10.0, DoorX1 = 10.8;                                           // DOOR, L300
        public const double StartX = 1.0;                                                           // START_X, L302
        /// <summary>Lane extent of the static floor boxes: past the walls by more than HALF + the 0.5 m ledge scan.</summary>
        private const double FloorFrom = LeftLimit - 1.2, FloorTo = RightLimit + 1.2;

        /// <summary>
        /// The opening as a directed moment on the cue clock: 480 frames at 24 fps (<c>OPENING_FRAMES</c>, L269), control
        /// at 20 s (L8506; acceptance "control by 0:20"); no cut before it (the skip button is <see cref="SceneRunner.SkipOpening"/>,
        /// L8071). Peak 12.5 s: the pull-back lands at f300 (L7777–L7786).
        /// </summary>
        public static readonly DirectedMoment Wake = new DirectedMoment("wake", 20, 20, 20, 12.5);

        /// <summary>The <c>seen</c> key of the wake's label check (§4.5, L8107).</summary>
        public const string LabelWake = "labelWake";
        /// <summary>The wake's label check holds 3.2 s after the clip and may be cut by a move only after 2.5 s (L8108).</summary>
        public const double LabelWakeHold = 3.2, LabelWakeCancelAfter = 2.5;

        private readonly SpawnPoint[] _spawns =
        {
            new SpawnPoint("start", StartX),                                                        // CHECKPOINTS, L7976
            new SpawnPoint("shutter", 2.9),                                                         // L7977
            new SpawnPoint("hall", 8.35),                                                           // L7978
            new SpawnPoint("door", 9.62),                                                           // L7979
        };

        private readonly CheckpointRule[] _rules =
        {
            CheckpointRule.When("shutter", LatchId, "release(), L1677"),
            CheckpointRule.Past("hall", PitX1 + 0.2, -0.05, "L2065"),
            CheckpointRule.When("door", DoorId, "the crank's last stroke, L1890"),
        };

        private readonly CueRule[] _cues =
        {
            new CueRule { Cue = "hall", AfterX = HallX + 0.2, UnlessEngaged = DoorId, HeardAfter = "hall", Cite = "L2066, heardHall L8087" },
            new CueRule { Cue = "threshold", WhenEngaged = DoorId, HeardAfter = "door", Cite = "L1890" },
        };

        private readonly SceneOpening _opening = new SceneOpening
        {
            Moment = Wake,
            Cue = "wake",                                                                           // Music.play('wake'), L8068
            Frames = 480,
            // captureChest (L7649–L7657) measures the label on frame 0 of the Opening clip at START_X. This is an estimate
            // (the slumped chest, facing +x); SceneHost replaces it with the label's measured centre.
            Chest = new Vec3(StartX + 0.1, 0.36, 0.0),
        };

        private readonly SceneExit _exit = new SceneExit
        {
            NextScene = "DL-02", X0 = DoorX0 + 0.15, X1 = DoorX1 - 0.15, OpenWhen = DoorId, RequireGrounded = true,
            Cite = "through the open door, L2039",
        };

        private readonly MechanismViewDef[] _views =
        {
            // The relay's three lamps (L1534–L1548).
            MechanismViewDef.On("PulseSequencer", RelayId, "RelayLamp0", ViewChannel.Lamp, ViewMotion.Emission, "L1543").Lamp(0),
            MechanismViewDef.On("PulseSequencer", RelayId, "RelayLamp1", ViewChannel.Lamp, ViewMotion.Emission, "L1543").Lamp(1),
            MechanismViewDef.On("PulseSequencer", RelayId, "RelayLamp2", ViewChannel.Lamp, ViewMotion.Emission, "L1543").Lamp(2),
            // The lever swings on its pivot, which rides the shutter (leverPivot is a child of shutterPivot, L1393–L1395).
            MechanismViewDef.On("Latch", LatchId, null, ViewChannel.LeverDeg, ViewMotion.RotateZ, "L278, L1694").About(3.24, 0.12, -0.02),
            MechanismViewDef.On("Latch", LatchId, null, ViewChannel.Position, ViewMotion.RotateZ, "L1693").Reading(ShutterId).About(ShutterPivotX, ShutterPivotY, 0),
            MechanismViewDef.On("Latch", LatchId, "LatchTag", ViewChannel.LeverDeg, ViewMotion.RotateZ, "L278, L1694").About(3.24, 0.12, -0.02),
            MechanismViewDef.On("Latch", LatchId, "LatchTag", ViewChannel.Position, ViewMotion.RotateZ, "L1693").Reading(ShutterId).About(ShutterPivotX, ShutterPivotY, 0),
            // The shutter and its rail swing about SHUTTER_PIVOT (L1390–L1392, L1693); the counterweight drops (L1697–L1699).
            MechanismViewDef.On("Door", ShutterId, null, ViewChannel.Position, ViewMotion.RotateZ, "L1693").About(ShutterPivotX, ShutterPivotY, 0),
            MechanismViewDef.On("Door", ShutterId, "ShutterRail", ViewChannel.Position, ViewMotion.RotateZ, "L1392").About(ShutterPivotX, ShutterPivotY, 0),
            MechanismViewDef.On("Door", ShutterId, "Counterweight", ViewChannel.ShutterCounterweightY, ViewMotion.TranslateY, "L1699").Scaled(1, -1.56),
            MechanismViewDef.On("Door", ShutterId, "CounterweightStripes", ViewChannel.ShutterCounterweightY, ViewMotion.TranslateY, "L1699").Scaled(1, -1.56),
            // The crank wheel turns −wheelAngle about (9.62, 0.45, three z −0.2) (L1401, L7959); the door rises with it (L7957).
            MechanismViewDef.On("CrankActuator", CrankId, null, ViewChannel.WheelDeg, ViewMotion.RotateZ, "L1401, L7959").Scaled(-1).About(9.62, 0.45, 0.2),
            MechanismViewDef.On("Door", DoorId, null, ViewChannel.Position, ViewMotion.TranslateY, "L7957"),
            // The cart: built at x 5.9 (CART1.x); dips nose-first and slides into the trench (tipInto, L4743–L4760).
            MechanismViewDef.On("TippingBridge", CartId, null, ViewChannel.BridgeDipDeg, ViewMotion.RotateZ, "L4750"),
            MechanismViewDef.On("TippingBridge", CartId, null, ViewChannel.BridgeX, ViewMotion.TranslateX, "L4759").Scaled(1, -5.9),
            MechanismViewDef.On("TippingBridge", CartId, null, ViewChannel.BridgeY, ViewMotion.TranslateY, "L4759"),
            // The scale's needle swings −95° (L4769).
            MechanismViewDef.On("LoadPlate", ScaleId, "ScaleNeedle", ViewChannel.Needle, ViewMotion.RotateZ, "L4769").Scaled(-95),
        };

        public override string Id => SceneId;
        public override string ArtRegion => "DL-01";
        public override double LaneX0 => LeftLimit;
        public override double LaneX1 => 12.0;                                                     // sceneName, L8135
        public override string FirstCheckpoint => "start";
        public override IReadOnlyList<SpawnPoint> Spawns => _spawns;
        public override IReadOnlyList<CheckpointRule> CheckpointRules => _rules;
        public override IReadOnlyList<CueRule> Cues => _cues;
        public override SceneOpening Opening => _opening;
        public override SceneExit Exit => _exit;
        public override IReadOnlyList<MechanismViewDef> Views => _views;

        /// <summary>
        /// The prototype's update order (§3.1): the relay pulse (#5, L8511), <c>updateMechanisms</c> (#6: the shutter,
        /// L1682), the latch and crank acts (#4, applied by their Step), then <c>updateCh1</c> (#7: the cart, the scale, L4752–L4769).
        /// </summary>
        public override void AddMechanisms(MechanismGraph g)
        {
            g.Add(new PulseSequencer(RelayId, PulseParams.Dl01Relay()));
            g.Add(new Latch(LatchId, LatchParams.Dl01Latch()));
            g.Add(new Door(ShutterId, DoorParams.Dl01Shutter()));
            g.Add(new CrankActuator(CrankId, CrankParams.Dl01Crank()));
            g.Add(new Door(DoorId, DoorParams.Dl01Door()));
            g.Add(new TippingBridge(CartId, TippingBridgeParams.Dl01Cart()));
            g.Add(new LoadPlate(ScaleId, LoadPlateParams.Dl01Scale()));
        }

        /// <summary><c>nearUse</c> (L1812–L1814) and the cart's push (<c>nearCh1</c>, L4274).</summary>
        public override void RegisterInteractables(MechanismGraph g, InteractionResolver r)
        {
            r.Register(g.Get<Latch>(LatchId));
            r.Register(g.Get<CrankActuator>(CrankId));
            r.Register(g.Get<TippingBridge>(CartId));
        }

        /// <summary><c>floorAt</c>/<c>surfaceAt</c>/<c>ceilingAt</c>/limits for region 1 (L1620–L1641, L1709–L1769, L4137–L4147).</summary>
        public override LaneGeometry BuildLane(MechanismGraph g)
        {
            return new LaneGeometry(LeftLimit, RightLimit)
                .Solid(FloorFrom, PitX0, 0)                                  // floorAt: 0, PIT.y inside (PIT.x0, PIT.x1), L1717
                .Solid(PitX0, PitX1, PitY)
                .Solid(PitX1, FloorTo, 0)
                .Solid(StepX0, StepX1, StepH)                                // PLATFORMS = [STEP], L298
                .Ceiling(FloorFrom, CeilingSplitX, CeilingLow)               // x < 2.6 ? 2.45 : 4, L1632
                .Ceiling(CeilingSplitX, FloorTo, CeilingHigh)
                .Add(new HingedCeiling(g.Get<Door>(ShutterId), ShutterPivotX, ShutterPivotY, ShutterPath))   // rotatedPath, L1620
                .Add(new WallUntilEngaged(g.Get<Latch>(LatchId), LockedLimit))                               // L1764
                .Add(new TippingBridgeLane(g.Get<TippingBridge>(CartId), TippingBridgeParams.Dl01Cart()));   // L4140, L4146
        }

        /// <summary>The relay's opening sets play from frame 0 (<c>sceneTime = 0</c>, L8061; <c>RELAY_SETS</c>, L332).</summary>
        public override void OnOpeningStart(SceneRunner runner) => runner.Graph.Get<PulseSequencer>(RelayId).SetClock(0);

        /// <summary>
        /// <c>startPlay</c> from the opening at <c>start</c> (natural end or skip): the label check, once per game
        /// (<c>labelWake</c>, L8105–L8109), with the <c>dispatch_item</c> voice.
        /// </summary>
        public override void OnControlReturned(SceneRunner runner, bool fromOpening)
        {
            if (!fromOpening || runner.Checkpoint != FirstCheckpoint || runner.HasSeen(LabelWake)) return;
            if (!runner.Motor.PlayQuirk(ClipNames.CheckLabel, cancel: false, holdFor: LabelWakeHold, cancelAfter: LabelWakeCancelAfter)) return;
            runner.MarkSeen(LabelWake);
            runner.Cue("dispatch_item");                                                            // Voice.play(dispatch_item), L8109
        }

        /// <summary>The label shot while he checks his label (L3735–L3741).</summary>
        public override ShotRequest? Shot(SceneRunner runner) => runner.LabelShot();

        /// <summary>Shakes from mechanism one-shots, and the trench's stuck act.</summary>
        public override void AfterMechanisms(SceneRunner runner)
        {
            MechanismLog log = runner.Graph.Log;
            for (int i = 0; i < log.Count; i++)
            {
                MechanismEvent e = log[i];
                if (e.Kind != MechanismEventKind.Event) continue;
                if (e.Id == ShutterId && e.Code == (int)DoorEvent.Cue) runner.Shake(0.9);                       // the counterweight's thud, L1679
                else if (e.Id == CrankId && e.Code == (int)CrankEvent.Stroke) runner.Shake(0.18);               // L1888
                else if (e.Id == CartId && e.Code == (int)TippingBridgeEvent.Land) runner.Shake(e.Value);       // L4757
                else if (e.Id == CartId && e.Code == (int)TippingBridgeEvent.Stranded) runner.Stuck();   // trenchStuck, L4765
            }
        }

        /// <summary>In the trench with no bridge: <c>trenchStuck</c> flinches and calls <c>respawn()</c> after 2.0 s (L4765, L4519–L4521; the motor's stuck act).</summary>
        public const double TrenchStuckSeconds = 2.0;
        /// <summary><c>respawn()</c>: the fade, then <c>startPlay</c> 1.3 s later on the game clock (L2997–L2999).</summary>
        public const double RespawnFadeSeconds = 1.3;
    }
}
