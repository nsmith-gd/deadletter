using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Dl06
{
    /// <summary>
    /// DL-06 Return to Sender (port_architecture §5, §4.13h; docs/scenes/DL-06_return_to_sender.md): the scanner reads room
    /// 114 and refuses it; the pit of dead letters is revealed; he checks his label and the belt starts, carrying a carrier
    /// toward the chute. Stop the belt, throw the points to the service ramp and start it again: from then the sorting floor
    /// is DL-07's (<c>sceneName</c>, L8141). Ridden to the chute, a carrier tips him onto the heap, and he is back at
    /// <c>scanned</c>. Region 3 below the gallery, from <c>REGION3_X</c> 60.3 (L2042, L8141). Lines are index.html at 7b3c123.
    /// <para><b>The shared floor.</b> DL-06 and DL-07 are one set and one carrier line (§5's cross-scene note). <see cref="Floor"/>
    /// builds what both stand on: the scanner and the dispatch hatch, the two levers, the line (with its dock, junction and chute
    /// tip) and DL-07's two weights, which lie on this floor from the start and are solid in its lane. In a chapter the
    /// floor is built once, by DL-06's definition: DL-07's shares its stretch and adds only the gallery, the loading of the
    /// weights and the bucket, with rules that extend <see cref="ReturnToSender06"/> (its virtual
    /// <see cref="ReturnToSender06.HasLeft"/> hands the floor over). <see cref="Floor"/> with DL-07's ID builds the whole
    /// floor again, for DL-07 simulated on its own.</para>
    /// </summary>
    public static class Dl06Scene
    {
        public const string Id = "DL-06";

        /// <summary>
        /// <c>REGION3_X</c> to <c>REGION4_X</c> (L2457, L3007): all of region 3, the floor, the chute and the heap he rides down
        /// to, which <c>sceneName</c> gives DL-06 or DL-07 by what has happened, not by x (L8141; <see cref="ReturnToSender06.HasLeft"/>).
        /// </summary>
        public const double X0 = Dl06Lane.Region3X, X1 = Dl06Lane.Region4X;

        /// <summary><c>SCANNER_X</c> (L2457); the scan starts within 0.06 of it (L2777) and draws him under it at rate 4 (L2784).</summary>
        public const double ScannerX = Dl06Lane.Off3 + 28.9, ScanReach = 0.06, ScanPull = 4;
        /// <summary><c>SCAN</c> (L2465): seconds from the scan's start.</summary>
        public const double ScanSweep = 0.5, ScanAnswer = 2.2, ScanRead = 2.8, ScanReject = 3.2, ScanHatch = 3.6, ScanReveal = 4.0, ScanCheck = 17.2;
        /// <summary>CheckLabel: perk at f56, done at f83 (L2809–L2810); <c>FPS</c> 24.</summary>
        public const double CheckPerkFrame = ClipTimings.CheckLabelEvents.Perk, CheckDoneFrame = ClipTimings.CheckLabelEvents.Done, Fps = 24;
        /// <summary><c>REVEAL_WALK</c>, <c>REVEAL_STOP_X</c> (L327): over the pit he walks to the rail at 0.65 by himself (L1934, L1980).</summary>
        public const double RevealWalk = 0.65, RevealStopX = Dl06Lane.Off3 + 35.9;
        /// <summary>He peers over the rail when he gets there (<c>REVEAL_STOP_X − 0.05</c>, L3868).</summary>
        public const double PeekX = RevealStopX - 0.05;

        /// <summary>The checkpoint after the label check (<c>CHECKPOINTS.scanned</c>: <c>OFF3 + 30.3</c>, L7986; <see cref="ChapterDefs.PrologueCheckpoints"/>).</summary>
        public const string ScannedCheckpoint = "scanned";
        public const double ScannedX = Dl06Lane.Off3 + 30.3;

        /// <summary>The levers' step-in and out speed (<c>game.z += … 0.4 · dt</c>, L2916): the motor's is 0.45 (M10).</summary>
        public const double LeverStepSpeed = 0.4;

        /// <summary><c>CHUTE</c> (L2463): where a tipped carrier sends him and the post, (x, y) at its top and its foot.</summary>
        public const double ChuteX0 = Dl06Lane.Off3 + 36.6, ChuteY0 = 0.0, ChuteX1 = Dl06Lane.Off3 + 39.3, ChuteY1 = -2.4;
        /// <summary><c>tipOut</c>/<c>updateFall</c> (L2977–L2994): 0.8 m/s down the chute, + 3.5 m/s², 0.1 above it; off its foot at
        /// 0.7 v forward and 0.6 v down; on the heap 0.05 above its height field; a second later, <c>respawn()</c>'s 1.3 s fade.</summary>
        public const double ChuteV0 = 0.8, ChuteAccel = 3.5, ChuteLift = 0.1, AirVx = 0.7, AirVy = 0.6, HeapLift = 0.05, DownFor = 1.0, Fade = 1.3;
        /// <summary><c>GRAVITY</c> (L306).</summary>
        public const double Gravity = 9.8;
        /// <summary><c>HEAP</c> (L2462): centre x and three.js z, spreads, peak and floor of its height field.</summary>
        public const double HeapX = Dl06Lane.Off3 + 41.5, HeapZ = -3.0, HeapSx = 4.2, HeapSz = 3.0, HeapPeak = -0.4, HeapFloor = -6.0;
        /// <summary>The carrier rail's Unity z (<c>RAIL_Z</c> −0.55, L2457).</summary>
        public const double RailZ = 0.55;

        /// <summary><c>heapH(x, z)</c> (L2468), with z in three.js's sign (− into the set).</summary>
        public static double HeapHeight(double x, double threeZ)
        {
            double dx = (x - HeapX) / HeapSx, dz = (threeZ - HeapZ) / HeapSz;
            return HeapFloor + (HeapPeak - HeapFloor) * Math.Exp(-(dx * dx + dz * dz));
        }

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => Floor(Id, "Return to Sender", () => new ReturnToSender06());

        /// <summary>The sorting floor as DL-06 and DL-07 share it, with <paramref name="rules"/>.</summary>
        public static SceneDef Floor(string id, string title, Func<SceneRules> rules) => new SceneDef
        {
            Id = id,
            Title = title,
            X0 = X0, X1 = X1,
            Region = Dl06Lane.Region,                                                                       // DL-06's checkpoint: scanned (L7986); DL-07's: landing, gallery
            Mechanisms = FloorMechanisms(),
            Interactables = FloorInteractables,
            Lane = Dl06Lane.Table,
            LaneContributors = Dl06Lane.Contributors,
            Motor = MotorTuning,
            Rules = rules,
        };

        /// <summary>
        /// The floor's mechanisms in step order, the prototype's: the weights move with his hands at #4 (<c>updateActCh1</c>);
        /// then <c>updateDL03</c> (#6): <c>updateScan</c> (the scanner; its belt start and its hatch carrier, L2798, L2813),
        /// the levers (thrown at #4, read by the belt), <c>updateCarriers</c> (L2694).
        /// </summary>
        public static MechanismDef[] FloorMechanisms() => new[]
        {
            new MechanismDef("dl07.weight0", () => new CarriedItem("dl07.weight0", WeightParams(Dl06Lane.Weight0X))),
            new MechanismDef("dl07.weight1", () => new CarriedItem("dl07.weight1", WeightParams(Dl06Lane.Weight1X))),
            new MechanismDef("dl06.scanner", () => new Dl06Scanner("dl06.scanner")),
            new MechanismDef("dl06.stopLever", () => new PointsLever("dl06.stopLever", PointsLeverParams.Dl06StopLever())),
            new MechanismDef("dl06.points", () => new PointsLever("dl06.points", PointsLeverParams.Dl06Points())),
            new MechanismDef("dl06.hatch", () => new Dl06Hatch("dl06.hatch", "dl06.scanner")),
            new MechanismDef("dl06.line", () => new CarrierLine("dl06.line", LineParams())),
        };

        /// <summary>The line as he boards it, only once the scan is done (<c>boardable()</c>: <c>game.scan.phase === 'done'</c>, L2855).</summary>
        public static IInteractable[] FloorInteractables(MechanismGraph g)
            => new IInteractable[] { new Dl06Ride(g.Get<CarrierLine>("dl06.line").Rider, g.Get<Dl06Scanner>("dl06.scanner")) };

        /// <summary>The return line (<see cref="CarrierLineParams.Dl06Line"/>) with the dispatch hatch at the scan's HATCH beat.</summary>
        public static CarrierLineParams LineParams()
        {
            var p = CarrierLineParams.Dl06Line();
            p.Hatch = "dl06.hatch";
            return p;
        }

        /// <summary>
        /// A sorting weight (<c>HP.weights</c>, L3893; <c>itemsHere</c> L4262: h <c>WEIGHT_H</c>, r <c>WEIGHT_R</c>, below
        /// <c>BAIL_BELOW_WRIST</c>; L320): on the floor at its home after every reset (<c>resetCh1</c>, L4098), solid to 0.22
        /// within 0.1 of its x (L4154). DL-07 loads them.
        /// </summary>
        public static CarriedItemParams WeightParams(double x) => new CarriedItemParams
        {
            HomeX = x, HomeBaseY = 0,
            Radius = Dl06Lane.WeightR, Half = Dl06Lane.WeightR, Height = Dl06Lane.WeightH,
            BelowWrist = 0.28,
        };

        /// <summary>
        /// The motor's tuning here: the prototype's, but the levers step in and out at 0.4 m/s (L2902, L2916), where the
        /// motor's station step-in is 0.45 (M10: <see cref="MotorConfig.StepInSpeed"/> is one speed for every station).
        /// Nothing else on this floor steps off the lane, so the scene sets it for the floor.
        /// </summary>
        public static MotorConfig MotorTuning()
        {
            var c = MotorConfig.Prototype();
            c.StepInSpeed = LeverStepSpeed;
            return c;
        }
    }

    /// <summary>
    /// DL-06's rules (port_architecture §5: "scanner sequence", "chute ride → heap → respawn, pit reveal"; the scanner, the
    /// levers and the line are mechanisms): the acts that hold him while the scanner reads him and while he checks his label
    /// (<c>updateScan</c>, L2774–L2818); over the pit, the walk to the rail by himself, slowly (L1934, L1980, <c>paceSlow</c>
    /// L2080) and the look over it (L3868); the <c>scanned</c> checkpoint (L2813); Proud after throwing the points to the
    /// exit (L2907); the Startle when a carrier's tip bangs down near him (L2735); the fall down the chute onto the heap and
    /// the respawn (<c>tipOut</c>, <c>updateFall</c>, L2976–L2994); and when the floor becomes DL-07's (<c>sceneName</c>, L8141).
    /// </summary>
    public class ReturnToSender06 : SceneRules
    {
        public static readonly CueId ShotScan = CueId.Of("shot:scan"), ShotPit = CueId.Of("shot:pit"), ShotCheck = CueId.Of("shot:check"),
            MusicDead = CueId.Of("music:dead"), VoiceTanScanner = CueId.Of("voice:tan_scanner");
        /// <summary>A camera shake; the argument is its amount in hundredths (<c>shake(0.25)</c> → 25).</summary>
        public static readonly CueId Shake = CueId.Of("shake");

        private Dl06Scanner _scanner;
        private CarrierLine _line;
        private PointsLever _points;
        private Dl06ScanAct _scan;
        private bool _peeked, _proud;

        public Dl06Scanner Scanner => _scanner;
        public CarrierLine Line => _line;
        public PointsLever StopLever { get; private set; }
        public PointsLever Points => _points;
        /// <summary>He has looked over the rail during the reveal (<c>game.scan.peeked</c>, L3869).</summary>
        public bool Peeked => _peeked;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _scanner = g.Get<Dl06Scanner>("dl06.scanner");
            _line = g.Get<CarrierLine>("dl06.line");
            StopLever = g.Get<PointsLever>("dl06.stopLever");
            _points = g.Get<PointsLever>("dl06.points");
            _scanner.OnSortingFloor = () => sim.Region == Dl06Lane.Region && !Upper(sim);                  // L2777
            _scanner.Climbing = () => sim.Motor.IsMantling;                                                // L2807
            _line.Clock = sim.Clock;                                                                       // game.clock (the payload's seed, L2666)
            _scan = null;
            _peeked = _proud = false;                                                                      // resetWorld: a new game.scan, L8031
        }

        /// <summary>On the gallery (<c>game.upper</c>): never in DL-06; DL-07's.</summary>
        protected virtual bool Upper(ChapterSim sim) => false;

        /// <summary>
        /// The floor is DL-07's (<c>sceneName</c>, L8141): on the gallery, past <c>landing</c>, or once the belt runs with the
        /// points set to the exit. DL-07's rules (on the same floor) decide their own way on.
        /// </summary>
        public override bool HasLeft(ChapterSim sim)
            => _line != null && (Upper(sim) || sim.Checkpoints.Current.Past("landing") || (_line.Route == CarrierRoute.Exit && _line.Running));

        /// <summary>
        /// #4's head (<c>updatePlayer</c> L1932–L1934, L1978–L1980): over the pit, with no stick, he walks on toward the rail
        /// (<c>move = 1</c> until <c>REVEAL_STOP_X</c>), at <c>REVEAL_WALK</c> (<c>paceSlow</c>, L2080).
        /// </summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            bool reveal = sim.Region == Dl06Lane.Region && _scanner.Phase == Dl06ScanPhase.Reveal;
            if (reveal && input.Move == 0 && sim.Motor.X < Dl06Scene.RevealStopX) { input.Move = 1; input.MoveIsAnalog = false; }
            sim.Motor.SlowWalkLimit = reveal ? Dl06Scene.RevealWalk : 0;
        }

        /// <summary>
        /// #4's tail: Proud once he has stepped back from throwing the points to the exit (the lever act's <c>'out'</c> end,
        /// L2905–L2907; the lever reports it at the clip's end, <see cref="PointsLeverEvent.Proud"/>).
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            if (_proud && sim.MotorActEndedOn == _points)
            {
                _proud = false;
                SceneQuirk.Start(sim, ClipNames.Proud, cancel: true);
            }
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            // updateScan (#6, L2774–L2815), on the scanner's transitions.
            if (log.Has("dl06.scanner", MechanismEventKind.State, (int)Dl06ScanPhase.Scan))
            {
                // game.act = scan, vx = 0, facing = 1 (L2778): the act holds his pose and draws him under the arch.
                var m = sim.Motor;
                _scan = new Dl06ScanAct(m.X, m.Y, m.Z, m.Yaw, sim.Config.YawRate);
                sim.StartAct(_scan);
                sim.Cue(ShotScan);
            }
            if (log.Has("dl06.scanner", MechanismEventKind.Event, (int)Dl06ScanEvent.Reject)) { sim.Cue(MusicDead); sim.Cue(VoiceTanScanner); }   // L2797
            if (log.Has("dl06.scanner", MechanismEventKind.State, (int)Dl06ScanPhase.Reveal))
            {
                // game.act = null (L2799): he is free where the scan drew him; the camera goes to the heap.
                if (_scan != null && ReferenceEquals(sim.Act, _scan)) { sim.EndAct(); sim.Motor.Place(_scan.X, _scan.Y, 1); }
                _scan = null;
                sim.Cue(ShotPit);
            }
            if (log.Has("dl06.scanner", MechanismEventKind.State, (int)Dl06ScanPhase.Check))
            {
                // game.act = check with CheckLabel until the scanner is done (L2808–L2812): a hold the scanner ends, which the
                // motor's quirk cannot be (#28: no way to end a motor act from outside), so a scene act; and vx = 0, which
                // only Place can do (M9).
                SceneQuirk.Stop(sim);
                sim.StartAct(new HoldAct("dl06.scanner", "Check", double.PositiveInfinity));
                sim.Cue(ShotCheck);
            }
            if (log.Has("dl06.scanner", MechanismEventKind.State, (int)Dl06ScanPhase.Done))
            {
                if (sim.Act != null && sim.Act.Kind == "dl06.scanner") sim.EndAct();                       // L2812
                sim.Checkpoints.Reach(Dl06Scene.ScannedCheckpoint);                                        // L2813
            }
            // The points thrown to the exit: Proud when he has stepped back (L2907).
            if (log.Has("dl06.points", MechanismEventKind.Event, (int)PointsLeverEvent.Proud)) _proud = true;
            // updateCarriers (#6): the tip bangs down near him (L2735); it tips him into the chute with the post (L2733).
            if (log.Has("dl06.line", MechanismEventKind.Event, (int)CarrierLineEvent.Startle))
            {
                sim.Cue(Shake, 25);
                SceneQuirk.Start(sim, ClipNames.Startle, cancel: true);
            }
            if (log.Has("dl06.line", MechanismEventKind.Event, (int)CarrierLineEvent.RiderTipped) && sim.Motor.Ride != null)
                sim.StartAct(new Dl06ChuteFallAct(sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config.YawRate));       // tipOut, L2976–L2980
            // updateQuirkTriggers (#10): over the pit, at the rail, he looks down (L3868–L3870).
            if (sim.Region == Dl06Lane.Region && _scanner.Phase == Dl06ScanPhase.Reveal && !_peeked && !sim.Busy
                && sim.X >= Dl06Scene.PeekX && sim.Grounded)
            {
                _peeked = true;
                SceneQuirk.Start(sim, ClipNames.PeekDown, cancel: false);
            }
        }
    }

    /// <summary>
    /// The scan (<c>game.act = { kind: 'scan' }</c>, L2778–L2799): he stands to attention under the arch while the scanner
    /// reads him, drawn toward <c>SCANNER_X</c> at rate 4 each step (<c>game.x += (SCANNER_X − x) · min(1, dt · 4)</c>, L2784),
    /// turning only to face +x (<c>updateCharacter</c>). It owns his pose; the rules end it at the reveal and hand the motor
    /// the spot (<see cref="ChapterSim.EndAct"/>). Its first step is the one after the scan started (L2778 returns).
    /// </summary>
    public sealed class Dl06ScanAct : SceneAct
    {
        private readonly double _yawRate;

        public Dl06ScanAct(double x, double y, double z, double yaw, double yawRate) : base("dl06.scanner", "Scan")
        {
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = yawRate;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            X += (Dl06Scene.ScannerX - X) * Math.Min(1, dt * Dl06Scene.ScanPull);                         // L2784 (at #6; nothing reads x between)
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);                              // facing = 1
            return true;
        }
    }

    /// <summary>
    /// Down the chute onto the heap (<c>tipOut</c>/<c>updateFall</c>, L2976–L2994): the tipping carrier sends him down the chute
    /// with the post (0.8 m/s, +3.5 m/s², 0.1 above it, on the rail's z), off its foot into the air (0.7 v forward, 0.6 v
    /// down, gravity) onto the heap's height field (+0.05), where he lies; a second later the fade, and the respawn at the
    /// checkpoint 1.3 s on (<c>respawn()</c>, L2997–L2999). It owns his pose; his yaw turns to face +x.
    /// </summary>
    public sealed class Dl06ChuteFallAct : SceneAct
    {
        private readonly double _yawRate, _len;
        private double _s, _v, _vx, _vy;
        private bool _faded;

        public Dl06ChuteFallAct(double x, double y, double z, double yaw, double yawRate) : base("dl06.chute", "Chute")
        {
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = yawRate;
            _v = Dl06Scene.ChuteV0;
            double dx = Dl06Scene.ChuteX1 - Dl06Scene.ChuteX0, dy = Dl06Scene.ChuteY1 - Dl06Scene.ChuteY0;
            _len = Math.Sqrt(dx * dx + dy * dy);                                                           // Math.hypot
        }

        public override bool OwnsPose => true;
        /// <summary>The fade has started (the respawn is pending).</summary>
        public bool Faded => _faded;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                       // a.t += dt (updateAct, L1840)
            switch (Phase)
            {
                case "Chute":
                {
                    _v += Dl06Scene.ChuteAccel * dt; _s += _v * dt;
                    double k = Math.Min(1, _s / _len);
                    X = Dl06Scene.ChuteX0 + (Dl06Scene.ChuteX1 - Dl06Scene.ChuteX0) * k;
                    Y = Dl06Scene.ChuteY0 + (Dl06Scene.ChuteY1 - Dl06Scene.ChuteY0) * k + Dl06Scene.ChuteLift;
                    Z = Dl06Scene.RailZ;
                    if (k >= 1) { Phase = "Air"; _vx = _v * Dl06Scene.AirVx; _vy = -_v * Dl06Scene.AirVy; }
                    break;
                }
                case "Air":
                {
                    _vy -= Dl06Scene.Gravity * dt; X += _vx * dt; Y += _vy * dt;
                    double floor = Dl06Scene.HeapHeight(X, -Z) + Dl06Scene.HeapLift;
                    if (Y <= floor) { Y = floor; Phase = "Down"; T = 0; sim.Cue(ReturnToSender06.Shake, 60); }
                    break;
                }
                case "Down":
                    if (T > Dl06Scene.DownFor && !_faded) { _faded = true; sim.RespawnAt = sim.Clock + Dl06Scene.Fade; }   // respawn(), L2997–L2999
                    break;
            }
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);                              // yawOverride = null, facing = 1
            return true;                                                                                   // until the respawn rebuilds the world
        }
    }

    /// <summary>
    /// The return line as he boards it from DL-06's floor: the line's <see cref="CarrierRide"/>, answering only once the scan
    /// is done (<c>boardable()</c> and <c>nearUse3</c>: <c>game.scan.phase !== 'done'</c> → nothing, L2855, L2867).
    /// </summary>
    public sealed class Dl06Ride : IRide
    {
        private readonly IRide _ride;
        private readonly IEngageable _scanned;

        public Dl06Ride(IRide ride, IEngageable scanned)
        {
            _ride = ride ?? throw new ArgumentNullException(nameof(ride));
            _scanned = scanned ?? throw new ArgumentNullException(nameof(scanned));
        }

        public InteractionCategory Category => _ride.Category;
        public bool IsAvailable(in InteractionQuery q) => _scanned.Engaged && _ride.IsAvailable(q);
        public bool OfferBoard(in InteractionQuery q, out int token, out double distance) => _ride.OfferBoard(q, out token, out distance);
        public bool RidePose(int token, out double x, out double y, out double z) => _ride.RidePose(token, out x, out y, out z);
        public RideStatus Status(int token) => _ride.Status(token);
        public double AlightY(int token) => _ride.AlightY(token);
        public void OnBoarding(int token) => _ride.OnBoarding(token);
        public void OnMounted(int token) => _ride.OnMounted(token);
        public void OnAlighted() => _ride.OnAlighted();
    }
}
