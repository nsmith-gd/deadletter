using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Dl10
{
    /// <summary>
    /// DL-10 Up Only (port_architecture §5; docs/scenes/DL-10_up_only.md §1–9 and its passes): off the balcony's end into
    /// ring C's relocation-lift lobby (<c>uponly</c>, zone <c>uo</c>). The lift only goes up, and won't go empty: its UP buzzes
    /// (he startles, the first time). The C-114 suitcase from the left luggage carried into the car's doorway and set on its
    /// floor plate: the needle swings, the gate draws shut, the UP lamps glow; the lobby's UP then sends the car up 1.6 m and
    /// back (the counterweight down its shaft and back, empty). The service crank winds the striped door up out of the lane
    /// (four strokes; a move lets go, it holds where left); on the counterweight's footplate its own service UP sends the
    /// car up for good with the suitcase, and he rides the counterweight down to ring C's level (the <c>ringc</c> directed
    /// moment, the cold light down the shaft); his again by 22 s, he walks on into region 5 past <c>REGION5_X</c>, where DL-11
    /// begins. Region 4, from <c>UPONLY.x0</c>; nothing kills here. Lines are index.html at 7b3c123 (L3455–L3461,
    /// L4526–L4675, L4937).
    /// <para><b>After DL-09.</b> DL-10 starts where DL-09 ends (<c>UPONLY.x0</c>) and reads nothing of it: the deck is
    /// <c>GALLERY.h</c> throughout region 4. Its checkpoint is <c>uponly</c>; <c>ringc</c>, past ring C's barricade, is DL-11's.
    /// It hands region 5 to DL-11 with the car gone for good (up, with the suitcase in it), the counterweight down at ring C's
    /// level, the service door up, and the <c>ringc</c> moment playing on.</para>
    /// <para>Not ported here: the voice <c>card_lastcar</c> and the tannoy <c>tan_relocation</c> (voices), the ambience's
    /// <c>order</c> → <c>heaps</c> × 0.6 once the car has gone (audio rules, L8154), the lobby hidden for the city shot and its
    /// lights, lamps, gauges and ropes (the view's, from <see cref="UpOnly10"/>'s mechanisms; its light zone is <see cref="Dl10Lane.LightZone"/>), the camera's lobby → shaft framing
    /// and the <c>car10</c> → <c>ringc10</c> shot (<c>Camera/MomentShots.RingC</c>), the idle hints.</para>
    /// </summary>
    public static class Dl10Scene
    {
        public const string Id = "DL-10";
        public const int Region = Dl10Lane.Region;

        /// <summary>Its checkpoint (<see cref="ChapterDefs.PrologueCheckpoints"/>): <c>uponly</c>, grounded past <c>UPONLY.x0 + 0.4</c> (L4937).</summary>
        public const string UpOnlyCheckpoint = "uponly";
        public const double UpOnlyFrom = Dl10Lane.X0 + 0.4;
        /// <summary>The once-only startle at the first buzz (<c>once('uoBuzz')</c>, L4595).</summary>
        public const string SeenBuzz = "uoBuzz";
        /// <summary>A buzz within 1.5 s of the act's end startles him 0.2 s later, unless he is busy or holding (L4595).</summary>
        public const double StartleWithin = 1.5, StartleAfter = 0.2;

        public static readonly CueId Shake = CueId.Of("shake"), MomentRingC = CueId.Of("moment:ringc"), PipsCar10 = CueId.Of("pips:car10");
        /// <summary>Shakes × 100: the car goes 0.15 (L4585), the crank's stroke 0.12 (L4569), the gate's slam 0.12 (L4624); its arrival is the lift's (0.35 with him, 0.12 without, L4631).</summary>
        public const int GoShake = 15, StrokeShake = 12, SlamShake = 12;

        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "Up Only",
            X0 = Dl10Lane.X0, X1 = Dl10Lane.X1,                                                          // sceneName, L8142; REGION5_X, L2047
            Region = Region,
            Mechanisms = Mechanisms(),
            Lane = Dl10Lane.Table,
            LaneContributors = Dl10Lane.Contributors,
            Interactables = CarLoader,
            Rules = () => new UpOnly10(),
        };

        /// <summary>
        /// In the prototype's order: the suitcase (moved by the acts at #4), the car's plate and gate, the two UP buttons and
        /// the crank (their acts are #4's: <c>updateAct10</c>), the service door, then the lift (<c>updateUpOnly</c> in
        /// <c>updateCh1</c>, #7), which reads the plate, the gate and this step's press.
        /// </summary>
        public static MechanismDef[] Mechanisms() => new[]
        {
            new MechanismDef("dl10.case", () => new CarriedItem("dl10.case", CaseParams())),
            new MechanismDef("dl10.carPlate", () => new LoadPlate("dl10.carPlate", LoadPlateParams.Dl10CarPlate())),
            new MechanismDef("dl10.carGate", () => new Door("dl10.carGate", PlateOutputs.Dl10CarGate())),
            new MechanismDef("dl10.upButton", () => new CallButton("dl10.upButton", CallButtonParams.Dl10UpButton())),
            new MechanismDef("dl10.serviceUp", () => new CallButton("dl10.serviceUp", CallButtonParams.Dl10ServiceUp())),
            new MechanismDef("dl10.serviceCrank", () => new CrankActuator("dl10.serviceCrank", CrankParams.Dl10ServiceCrank())),
            new MechanismDef("dl10.serviceDoor", () => new Door("dl10.serviceDoor", DoorParams.Dl10ServiceDoor())),
            new MechanismDef("dl10.lift", () => new RelocationLift("dl10.lift", RelocationLiftParams.Dl10Lift())),
        };

        /// <summary>
        /// The C-114 suitcase (<c>itemsHere</c>, L4263: h 0.2, r <c>UO.caseHalf</c> 0.16, below 0.24; heavy: he carries it slowly
        /// and cannot jump): on the deck at <c>UO.caseX</c>, or in the car (its plate's, seat 0) past <c>ringc</c> (<c>resetCh1</c>,
        /// L4103). In the car it keeps its lane x and base, as the prototype's does (the view sets it on the plate, L4666).
        /// </summary>
        public static CarriedItemParams CaseParams() => new CarriedItemParams
        {
            HomeX = Dl10Lane.CaseX, HomeBaseY = Dl10Lane.Deck,
            Radius = Dl10Lane.CaseHalf, Half = Dl10Lane.CaseHalf, Height = SuitcaseLane.Height, BelowWrist = 0.24,     // L4263
            MovedAfter = "ringc", MovedState = ItemState.Placed, MovedX = Dl10Lane.CaseX, MovedBaseY = Dl10Lane.Deck, MovedSlot = 0,
        };

        public static IInteractable[] CarLoader(MechanismGraph g) => new IInteractable[]
        {
            new Dl10CarLoader(g.Get<CarriedItem>("dl10.case"), g.Get<RelocationLift>("dl10.lift")),
        };

        /// <summary><c>RINGC_LIGHT</c> (L4610): the cold light down the shaft ramps from 9.5 s to 12 s on the cue, off over 1.5 s from 20 (or from his release).</summary>
        public const double ColdLightFrom = 9.5, ColdLightFull = 12, ColdLightOff = 20, ColdLightFade = 1.5;

        /// <summary>
        /// The cold light's level, 0..1 (× 2.6 is the prototype's intensity, L4619): <c>smooth((t − 9.5) / 2.5) · (1 − smooth((t −
        /// off) / 1.5))</c> on the <c>ringc</c> cue's time while he has ridden, off = min(his release, 20).
        /// </summary>
        public static double ColdLight(double? cueTime, double? lightOff)
        {
            if (cueTime == null) return 0;
            double t = cueTime.Value, off = Math.Min(lightOff ?? ColdLightOff, ColdLightOff);
            return Smooth.Step((t - ColdLightFrom) / (ColdLightFull - ColdLightFrom)) * (1 - Smooth.Step((t - off) / ColdLightFade));
        }
    }

    /// <summary>
    /// The suitcase into the car (<c>nearCh1</c>'s <c>loadCar</c>, L4212; <c>beginCh1</c> L4315; <c>updateAct10</c> L4543–L4561): with
    /// the suitcase in his hands within 0.25 of the car's doorway while the lift is idle, he walks to <c>UO.car.mid</c>, faces
    /// +1, turns into the set, steps 0.5 into the doorway, sets it on the floor plate with SetDown and steps back out. At f14
    /// it is in the car (<see cref="ItemState.Placed"/>, seat 0), which the plate (<c>dl10.carPlate</c>) weighs from this step's
    /// mechanisms. The motor plays the act; this answers where he stands and takes the suitcase.
    /// </summary>
    public sealed class Dl10CarLoader : IPlaceTarget
    {
        /// <summary>The doorway's reach (L4212) and how far he steps into it (three z −0.5, L4546).</summary>
        public const double Reach = 0.25, InZ = 0.5;

        private readonly CarriedItem _case;
        private readonly RelocationLift _lift;

        public Dl10CarLoader(CarriedItem suitcase, RelocationLift lift)
        {
            _case = suitcase ?? throw new ArgumentNullException(nameof(suitcase));
            _lift = lift ?? throw new ArgumentNullException(nameof(lift));
        }

        public InteractionCategory Category => InteractionCategory.Item;
        public string Clip => ClipNames.SetDown;
        public bool TurnIntoSet => true;

        /// <summary>L4212: the suitcase in his hands (<c>game.carry.key === 'case'</c>), by the doorway, the lift idle.</summary>
        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            pose = default;
            if (q.Hold != HoldKind.Item || !Accepts(q.Carried)) return false;
            if (!(q.X > Dl10Lane.CarX0 - Reach && q.X < Dl10Lane.CarX1 + Reach) || _lift.State != RelocationLiftState.Idle) return false;
            pose = new StationPose(Dl10Lane.CarMid, +1, InZ);
            return true;
        }

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);

        public bool Accepts(ICarryable item) => ReferenceEquals(item, _case);

        /// <summary>SetDown f14 (L4553–L4554): <c>it.state = 'car'</c>, its x and base kept; the plate feels it at this step's #6.</summary>
        public void OnPlaced(ICarryable item)
        {
            if (!Accepts(item)) return;
            _case.MoveTo(ItemState.Placed, _case.X, _case.BaseY, 0);
        }
    }

    /// <summary>
    /// DL-10's rules: <c>uponly</c> (L4937); the UP buttons' outcomes (the car goes: shake 0.15; it buzzes: the panel's buzz,
    /// the Pips' <c>car10</c> flash while the car is empty, and the first time ever a Startle 0.2 s after the act, L4584–L4595);
    /// the ride (<see cref="Dl10RideAct"/>, from PressButtonHigh f34 on the counterweight's panel with the car sent, L4592) and
    /// the <c>ringc</c> moment it starts (L4588), whose cue clock the car follows (L4616–L4617); the cold light's switch-off
    /// (<c>uo.lightOff</c>, L4606); the shakes (the crank's strokes, the gate's slam, the car's arrival); and the hand-off to
    /// region 5 past <c>REGION5_X</c> (L2047, free movement only).
    /// <para>Its hooks run while DL-10 holds him; what they guard by region and x is DL-10's stretch.</para>
    /// </summary>
    public sealed class UpOnly10 : SceneRules
    {
        private CarriedItem _case;
        private RelocationLift _lift;
        private CallButton _up, _serviceUp;
        private CrankActuator _crank;
        private Door _gate, _serviceDoor;
        private double _buzzAt, _startleAt;

        public CarriedItem Case => _case;
        public LoadPlate CarPlate { get; private set; }
        public Door CarGate => _gate;
        public CallButton UpButton => _up;
        public CallButton ServiceUp => _serviceUp;
        public CrankActuator Crank => _crank;
        public Door ServiceDoor => _serviceDoor;
        public RelocationLift Lift => _lift;
        /// <summary>The <c>ringc</c> moment's clock and state (<c>startMoment('ringc')</c>; the runtime schedules its cue).</summary>
        public MomentDirector Moment { get; } = new MomentDirector(null);
        /// <summary>The last buzz's game clock (<c>uo.buzz</c>, −100 after a reset, L4102): the UP lamps stutter for 0.9 s after it.</summary>
        public double BuzzAt => _buzzAt;
        /// <summary>The cue time at which he was let go on ring C's level (<c>uo.lightOff</c>): the cold light goes off from there (L4606, L4618).</summary>
        public double? LightOff { get; internal set; }
        /// <summary>The cold light's level now, 0..1 (<see cref="Dl10Scene.ColdLight"/>): only once he has ridden.</summary>
        public double ColdLight(double clock) => Dl10Scene.ColdLight(_lift.Riding ? Moment.Time(clock) : null, LightOff);

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _case = g.Get<CarriedItem>("dl10.case");
            CarPlate = g.Get<LoadPlate>("dl10.carPlate");
            _gate = g.Get<Door>("dl10.carGate");
            _up = g.Get<CallButton>("dl10.upButton");
            _serviceUp = g.Get<CallButton>("dl10.serviceUp");
            _crank = g.Get<CrankActuator>("dl10.serviceCrank");
            _serviceDoor = g.Get<Door>("dl10.serviceDoor");
            _lift = g.Get<RelocationLift>("dl10.lift");
            _gate.BindClock(() => sim.Clock);                                                               // game.clock − uo.loadedAt > 0.8, L4621
            Moment.End();                                                                                   // resetWorld: Music.endMoment(), L8017
            _buzzAt = -100;                                                                                 // uo.buzz, L4102
            _startleAt = double.NaN;
            LightOff = null;
        }

        /// <summary>
        /// #4's head: the Startle the first buzz set off (<c>setTimeout(…, 200)</c>, L4595) plays at the start of the step its
        /// 0.2 s are up, before the player's update, unless he is busy or holding something then.
        /// </summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            if (double.IsNaN(_startleAt) || sim.Clock < _startleAt - 1e-9) return;
            _startleAt = double.NaN;
            if (!sim.Busy && sim.Motor.Hold == HoldKind.None) sim.Motor.PlayQuirk(ClipNames.Startle, cancel: true);
        }

        /// <summary>
        /// #4's tail: while he rides, the car follows the cue's clock (read at #7, L4616: the same clock); an UP act that has
        /// ended at f34 (L4592–L4595): onto the ride if the counterweight's panel sent the car, else a Startle after the first
        /// buzz; into region 5 past <c>REGION5_X</c> (L2047).
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            var m = sim.Motor;
            if (_lift.Riding) FollowCue(sim);
            var ended = sim.MotorActEndedOn;
            if (ended != null && (ReferenceEquals(ended, _up) || ReferenceEquals(ended, _serviceUp)))
            {
                if (ReferenceEquals(ended, _serviceUp) && _lift.Riding)
                {
                    sim.StartAct(new Dl10RideAct(this, _lift, Moment, sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config));   // a.phase = 'ride', L4592
                    return;
                }
                if (sim.Clock - _buzzAt < Dl10Scene.StartleWithin && !sim.Checkpoints.HasSeen(Dl10Scene.SeenBuzz))
                {
                    sim.Checkpoints.MarkSeen(Dl10Scene.SeenBuzz);
                    _startleAt = sim.Clock + Dl10Scene.StartleAfter;
                }
            }
            bool free = freeStep || (!sim.Busy && !m.IsMantling);                                          // the prototype's free movement (holding too)
            if (free && sim.Region == Dl10Scene.Region && sim.X > Dl10Lane.X1) sim.SetRegion(Dl10Scene.Region + 1);   // L2047
        }

        internal void FollowCue(ChapterSim sim)
        {
            double? t = Moment.Time(sim.Clock);
            if (t != null) _lift.FollowCue(t.Value);
        }

        /// <summary>After the mechanisms (<c>updateUpOnly</c> and the checkpoints in <c>updateCh1</c>, #7).</summary>
        public override void AfterGraph(ChapterSim sim)
        {
            if (!double.IsNaN(_startleAt) && sim.Clock >= _startleAt - 1e-9) _startleAt = double.NaN;   // its step passed in an act: the timer is spent
            var log = sim.Graph.Log;
            for (int i = 0; i < log.Count; i++)
            {
                var e = log[i];
                if (e.Id == _lift.Id && e.Kind == MechanismEventKind.Event)
                {
                    switch ((RelocationLiftEvent)e.Code)
                    {
                        case RelocationLiftEvent.Go:                                                        // clunk, chain, shake 0.15 (L4585)
                            sim.Cue(Dl10Scene.Shake, Dl10Scene.GoShake);
                            if (e.Index == 1)                                                               // he rides: ringc (L4588)
                            {
                                Moment.Start(PrologueMoments.RingC, sim.Clock, musicAvailable: false);
                                sim.Cue(Dl10Scene.MomentRingC);
                            }
                            break;
                        case RelocationLiftEvent.Buzz:                                                      // L4590
                            _buzzAt = sim.Clock;
                            if (e.Index == 0) sim.Cue(Dl10Scene.PipsCar10);                                 // Pips.flash('car10'): the car is empty
                            break;
                        case RelocationLiftEvent.Arrive:                                                    // L4631
                            if (e.Value > 0) sim.Cue(Dl10Scene.Shake, (int)Math.Round(e.Value * 100));
                            break;
                    }
                }
                else if (e.Id == _crank.Id && e.Kind == MechanismEventKind.Event && e.Code == (int)CrankEvent.Stroke)
                    sim.Cue(Dl10Scene.Shake, Dl10Scene.StrokeShake);                                        // L4569
                else if (e.Id == _gate.Id && e.Kind == MechanismEventKind.State && e.Code == (int)DoorState.Open)
                    sim.Cue(Dl10Scene.Shake, Dl10Scene.SlamShake);                                          // the gate slams, L4624
            }
            // updateCh1's checkpoints (L4937).
            if (sim.Region == Dl10Scene.Region && sim.X > Dl10Scene.UpOnlyFrom && sim.Grounded) sim.Checkpoints.Reach(Dl10Scene.UpOnlyCheckpoint);
        }
    }

    /// <summary>
    /// The ride down (<c>game.act = { kind: 'ride10', phase: 'ride' }</c>, <c>updateAct10</c> L4597–L4607), from the step after
    /// PressButtonHigh's f34 on the counterweight's panel with the car sent: he stands on the counterweight's footplate as it
    /// was at the step's start (<c>game.x = UO.cw.stand</c>, <c>game.y = DECK − uo.d</c> at #4, before <c>updateUpOnly</c>: a step
    /// behind it), grounded, still, facing +1; RideCounterweight, then Idle once it has landed. Once the car has gone (5.5 s on
    /// the cue) the <c>ringc</c> moment lets him go (<c>momentFree</c>: at 22 s, or at a touch of the controls from 16 s), and
    /// the cold light goes off from that moment's time. It owns his pose: the motor's ride sync (#9) would put him on this
    /// step's counterweight, a step ahead of the prototype, and the motor has no act that holds him to a moving floor (#32).
    /// Kind <c>ride10</c>, phase <c>ride</c>.
    /// </summary>
    public sealed class Dl10RideAct : SceneAct
    {
        public static readonly ActId RideKind = ActId.Of("ride10"), RidePhase = ActId.Of("ride");

        private readonly UpOnly10 _rules;
        private readonly RelocationLift _lift;
        private readonly MomentDirector _moment;
        private readonly double _yawRate;

        public Dl10RideAct(UpOnly10 rules, RelocationLift lift, MomentDirector moment, double x, double y, double z, double yaw, MotorConfig c)
            : base(RideKind, RidePhase)
        {
            _rules = rules ?? throw new ArgumentNullException(nameof(rules));
            _lift = lift ?? throw new ArgumentNullException(nameof(lift));
            _moment = moment ?? throw new ArgumentNullException(nameof(moment));
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = c.YawRate;
        }

        /// <summary>The counterweight has landed with him (<c>a.landed</c>: the clip goes to Idle).</summary>
        public bool Landed { get; private set; }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                        // a.t (updateActCh1)
            X = Dl10Lane.CwStand; Y = _lift.CounterweightY;                                                 // L4600
            _rules.FollowCue(sim);                                                                          // the car's climb is the cue's (L4616)
            bool gone = _lift.State == RelocationLiftState.Gone;
            if (gone && !Landed) Landed = true;                                                             // L4603
            double? t = _moment.Time(sim.Clock);                                                            // L4604
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);                                      // facing 1: updateCharacter
            if (gone && _moment.Free(PrologueMoments.RingC, t, MomentDirector.AnyInput(input)))             // L4605–L4606
            {
                _rules.LightOff ??= t ?? 0;
                sim.Motor.Place(X, Y, 1, Yaw);
                return false;
            }
            return true;
        }
    }
}
