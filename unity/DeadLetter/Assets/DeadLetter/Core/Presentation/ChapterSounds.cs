using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Streaming;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// The prologue's sounds (DL-01 to DL-06, index.html <c>Sound.*</c> call sites in audio_inventory.md), decided from what a
    /// <see cref="ChapterSim"/> step reports, so they are tested without Unity (port_architecture §3.1 #10–#11):
    /// <list type="bullet">
    /// <item>the mechanisms' one-shots and transitions (<see cref="MechanismGraph.Log"/>, <c>Mechanism.Emit</c>/<c>Enter</c>);</item>
    /// <item>the motor's events (<see cref="D17Motor.Events"/>: footsteps, jumps, landings, clip changes, act frames, a death);</item>
    /// <item>the scenes' <c>sound:</c> cues (<see cref="ChapterSim.Cues"/>, through <see cref="CueRoutes"/>);</item>
    /// <item>what the prototype polls each frame: the racks' rows, wheels squeaking, the hatch winding, the depot's relay pulse
    /// and atmosphere (drips, the live cable, the steam, distant machinery);</item>
    /// <item>the continuous layers' levels (<see cref="Loops"/>: <c>Sound.hum/buzz/hiss/roll/tubes/belt/drag</c>).</item>
    /// </list>
    /// Call <see cref="Step"/> once after each <see cref="ChapterSim.Step"/>; the runtime plays <see cref="Sounds"/> (key,
    /// volume, lane x for the pan) and sets each layer to <see cref="Loop"/>. Random choices (squeaks, drips, crackles,
    /// distant clanks) are seeded (<see cref="AudioRng"/>), so a replay hears the same. A step allocates nothing.
    /// <para>Where the prototype's <c>setTimeout</c> delays a sound it is queued on the game clock (<see cref="SfxQueue.PlayAfter"/>).</para>
    /// </summary>
    public sealed class ChapterSounds
    {
        // index.html constants: OFF2/OFF3 (L274), the relay (L8515), the racks' rows (ROW_TIMES L2422), the tubes and the
        // belt's centres (L2428, L2830), the live cable (L7938), the steam (L7965), the press (L7349).
        public const double Off2 = AmbienceRules.Off2, Off3 = AmbienceRules.Off3;
        public const double RelayX = 2.0, RelayFadeFromX = Off3 + 57, RelayFadeOver = 7;
        public static readonly double[] RowTimes = { 1.0, 2.2, 3.4, 4.6, 5.8, 7.0 };
        public const double TubesX = Off2 + 21, TubesOver = 8, TubesFloor = 0.25;
        public const double BeltX = Off3 + 33, BeltOver = 9, BeltFloor = 0.2;
        public const double CableX = 8.0, CableOver = 6, CableFloor = 0.15, FirstCrackle = 4, CrackleMin = 3, CrackleSpread = 5, SparkFor = 0.18;
        public const double PressX = 13.95, GateX = Dl03Scene.GateX, ScannerX = Dl06Scene.ScannerX;
        /// <summary>The depot's work bulb in play: <c>Sound.buzz(bulb · 0.25)</c> with the bulb steady at 1 (L1574).</summary>
        public const double WorkBulbBuzz = 0.25;
        /// <summary>The trolley's roll: min(1, |v| / 0.5) (L2370); a ridden carrier 0.7 while it moves (L2969).</summary>
        public const double TrolleyRollSpeed = 0.5, RideRoll = 0.7;
        /// <summary>Dragging the courier or the body: min(1, speed / 0.22) (L4703).</summary>
        public const double DragSpeed = 0.22;
        /// <summary>Squeaks while a wheeled thing moves faster than 0.05 m/s: the DL-03 trolley 0.6 /s (L2350), others 0.8 /s (L4703).</summary>
        public const double SqueakAbove = 0.05, TrolleySqueakRate = 0.6, PushSqueakRate = 0.8;
        /// <summary>The DL-05 hatch winding: a ratchet about 6 /s (L4917).</summary>
        public const double HatchRatchetRate = 6;
        /// <summary>The mantle's sounds after its jump (L1910–L1911).</summary>
        public const double MantleScrape1 = 0.38, MantleStrain = 0.70, MantleScrape2 = 1.05, MantleClick = 1.40;
        /// <summary>The release's thud is the shutter's own cue (<see cref="DoorEvent.Cue"/> at 0.56 s, L1679); the tube's tap 0.2 s after its cough (L4772); the weigh-in's twitch clunk 0.26 s after its ratchet (L4909); the tumble 0.3 s after a carrier tips its parcels (L2730).</summary>
        public const double TubeTap = 0.2, TwitchClunk = 0.26, PayloadTumble = 0.3;

        private enum Kind
        {
            None, Relay, Latch, Shutter, Crank, Cart, TubeLetter, Press, Trolley, Plate, Gate, Courier, Cradle, Drum, Body,
            WeighIn, Hatch, Scanner, StopLever, Points, Line,
        }

        private sealed class Source
        {
            public Kind Kind;
            public IMechanism M;
        }

        /// <summary>The prologue's sounding mechanisms by ID (Core/Scenes/Dl0x).</summary>
        private static readonly KeyValuePair<string, Kind>[] Ids =
        {
            P("dl01.relay", Kind.Relay), P("dl01.latch", Kind.Latch), P("dl01.shutter", Kind.Shutter), P("dl01.crank", Kind.Crank),
            P("dl01.door", Kind.None), P("dl01.cart", Kind.Cart),
            P("dl02.tubeLetter", Kind.TubeLetter), P("dl02.press", Kind.Press),
            P("dl03.trolley", Kind.Trolley), P("dl03.plate", Kind.Plate), P("dl03.gate", Kind.Gate),
            P("dl04.courier", Kind.Courier), P("dl04.cradle", Kind.Cradle),
            P("dl05.drum", Kind.Drum), P("dl05.body", Kind.Body), P("dl05.weighIn", Kind.WeighIn), P("dl05.hatch", Kind.Hatch),
            P("dl06.scanner", Kind.Scanner), P("dl06.stopLever", Kind.StopLever), P("dl06.points", Kind.Points), P("dl06.line", Kind.Line),
        };

        private static KeyValuePair<string, Kind> P(string id, Kind k) => new KeyValuePair<string, Kind>(id, k);

        // Keys resolved once (string building is not per step).
        private static readonly string KStep = SfxKeys.Simple["step"], KJump = SfxKeys.Simple["jump"], KLand = SfxKeys.Simple["land"],
            KBonk = SfxKeys.Simple["bonk"], KTap = SfxKeys.Simple["tap"], KLift = SfxKeys.Simple["lift"], KScrape = SfxKeys.Simple["scrape"],
            KStrain = SfxKeys.Simple["strain"], KClick = SfxKeys.Simple["click"], KWorried = SfxKeys.Simple["worried"],
            KClank = SfxKeys.Simple["clank"], KThud = SfxKeys.Simple["thud"], KRatchet = SfxKeys.Simple["ratchet"],
            KDoorRumble = SfxKeys.Simple["doorRumble"], KDoorOpen = SfxKeys.Simple["doorOpen"], KPlate = SfxKeys.Simple["plate"],
            KGateTick = SfxKeys.Simple["gateTick"], KGateSlam = SfxKeys.Simple["gateSlam"], KSqueak = SfxKeys.Simple["squeak"],
            KClunk = SfxKeys.Simple["clunk"], KTick = SfxKeys.Simple["tick"], KBuzzShort = SfxKeys.Simple["buzzShort"],
            KAlarmBell = SfxKeys.Simple["alarmBell"], KScanSweep = SfxKeys.Simple["scanSweep"], KChirp = SfxKeys.Simple["chirp"],
            KReject = SfxKeys.Simple["reject"], KKlaxon = SfxKeys.Simple["klaxon"], KBeltStop = SfxKeys.Simple["beltStop"],
            KClack = SfxKeys.Simple["clack"], KHatchLift = SfxKeys.Simple["hatchLift"], KBell = SfxKeys.Simple["bell"],
            KTumble = SfxKeys.Simple["tumble"], KDrip = SfxKeys.Simple["drip"], KCrackle = SfxKeys.Simple["crackle"],
            KDistant = SfxKeys.Simple["distant"], KGroan = SfxKeys.Simple["groan"],
            KSetDownFloor = SfxKeys.SetDown(false), KSetDownDeck = SfxKeys.SetDown(true),
            KCreakPull = SfxKeys.Creak(0.6), KCreakLatch = SfxKeys.Creak(0.4),
            KChainRelease = SfxKeys.Chain(0.55), KRattleRelease = SfxKeys.Rattle(0.9), KChainTube = SfxKeys.Chain(0.3),
            KChainServed = SfxKeys.Chain(1.5),
            KServoTug = SfxKeys.Servo(0.2, 500, 900), KServoLever = SfxKeys.Servo(0.15, 400, 700),
            KServoCradleDraw = SfxKeys.Servo(0.5, 260, 520), KServoCradleSeat = SfxKeys.Servo(0.6, 300, 700);
        private static readonly string[] KRelay = { SfxKeys.Relay(0), SfxKeys.Relay(1), SfxKeys.Relay(2) };
        private static readonly string[] KAnswer = { SfxKeys.Answer(0), SfxKeys.Answer(1), SfxKeys.Answer(2) };
        private static readonly string[] KRowOn = { SfxKeys.RowOn(0), SfxKeys.RowOn(1), SfxKeys.RowOn(2), SfxKeys.RowOn(3), SfxKeys.RowOn(4), SfxKeys.RowOn(5) };
        private static readonly string[] KDeath = { SfxKeys.Death("crush"), SfxKeys.Death("shock"), SfxKeys.Death("grabbed"), SfxKeys.Death("fall") };

        /// <summary>The depot's falling drops (<c>atmos.drips</c>: DL-01's three, L7852; DL-03's over the plate, L2226): x, height, first interval.</summary>
        private static readonly double[] DripX = { 1.45, 8.25, 6.85, Off2 + 15.4 }, DripY = { 0.62, 3.1, 2.5, 2.55 }, DripEvery = { 3.1, 2.3, 2.7, 3.4 };
        public const double DripHear = 6, DripNextMin = 2, DripNextSpread = 3;

        private readonly ChapterSim _sim;
        private readonly SfxQueue _q;
        private readonly CueRoutes _routes = new CueRoutes();
        private readonly Dictionary<string, Source> _byId = new Dictionary<string, Source>(StringComparer.Ordinal);
        private readonly double[] _loops = new double[SfxLoopMixer.Count];
        private readonly AudioRng _rng;
        private readonly AtmosphereRules _atmos;
        private readonly RacksReveal _reveal;
        private readonly Pushable _trolley, _courier, _drum, _body;
        private readonly Door _hatch;
        private readonly CarrierLine _line;
        // Atmosphere (updateAtmosphere, L7895–L7966): per drop its timer, interval and fall clock (−1 = waiting).
        private readonly double[] _dripT = new double[4], _dripEvery = new double[4], _dripFall = new double[4];
        private double _nextSpark = FirstCrackle, _puffNext = 1.5, _puffUntil;
        private int _rowsLit;
        private double _rowsFor = double.NaN;
        private ActId _lastActPhase, _lastActKind;
        private double _lastClock = double.NaN;
        private long _motorStep = -1;
        private int _motorSeen;

        public ChapterSounds(ChapterSim sim, uint seed = 23, SfxQueue queue = null)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            _q = queue ?? new SfxQueue();
            _rng = new AudioRng(seed);
            _atmos = new AtmosphereRules(seed * 2654435761u + 1);
            foreach (var p in Ids)
                if (sim.Graph.TryGet(p.Key, out IMechanism m)) _byId[p.Key] = new Source { Kind = p.Value, M = m };
            _trolley = Mech<Pushable>("dl03.trolley");
            _courier = Mech<Pushable>("dl04.courier");
            _drum = Mech<Pushable>("dl05.drum");
            _body = Mech<Pushable>("dl05.body");
            _hatch = Mech<Door>("dl05.hatch");
            _line = Mech<CarrierLine>("dl06.line");
            _reveal = sim.Def.Scene(Dl03Scene.Id) != null || sim.Def.Scene(Dl04Scene.Id) != null ? sim.Shared<RacksReveal>() : null;
            for (int i = 0; i < DripX.Length; i++)
            {
                _dripEvery[i] = DripEvery[i];
                _dripT[i] = i == 3 ? 1 : _rng.NextDouble() * DripEvery[i];                  // t: random·every (L7852); DL-03's t: 1 (L2226)
                _dripFall[i] = -1;
            }
        }

        private T Mech<T>(string id) where T : class, IMechanism => _byId.TryGetValue(id, out var s) ? s.M as T : null;

        public ChapterSim Sim => _sim;
        /// <summary>This step's one-shots (cleared at each <see cref="Step"/>).</summary>
        public SfxQueue Sounds => _q;
        /// <summary>The level each continuous layer is asked for (<see cref="SfxLoopMixer.Set"/>; the runtime's mixer glides it).</summary>
        public double Loop(SfxLoop loop) => _loops[(int)loop];
        /// <summary>Lit fraction of the racks' rows this step (0–1), for the tubes and the rack lights (L2414–L2427).</summary>
        public double RacksLit { get; private set; }

        /// <summary>
        /// Reads the step that just ran. <paramref name="voicesHeld"/>: a voice is playing or a moment's shot holds
        /// (<c>voicesHeld()</c>, L7964), which keeps the distant machinery waiting; <paramref name="calm"/>: the rows light
        /// with the calm curve (L2418).
        /// </summary>
        public void Step(bool voicesHeld = false, bool calm = false)
        {
            var sim = _sim;
            double now = sim.Clock;
            double dt = double.IsNaN(_lastClock) || now < _lastClock ? ChapterSim.StepSeconds : now - _lastClock;
            _lastClock = now;
            _q.Clear();
            _q.Release(now);
            ReadCues(sim.Cues);
            ReadLog(sim.Graph.Log, now);
            ReadMotor(sim.Motor, now);
            ReadSceneAct();
            Poll(now, dt, calm);
            Atmosphere(now, dt, voicesHeld);
            SetLoops();
        }

        /// <summary>A new world (begin, continue, respawn): what was scheduled in the old one does not sound into it.</summary>
        public void OnPlaced()
        {
            _q.Reset();
            _lastActPhase = ActId.None;
            _lastActKind = ActId.None;
            _lastClock = double.NaN;
        }

        // ---- The scenes' cues ----------------------------------------------------------------------------------------------
        private void ReadCues(IReadOnlyList<Cue> cues)
        {
            for (int i = 0; i < cues.Count; i++)
            {
                CueRoute r = _routes.Resolve(cues[i].Id);
                if (r.Kind == CueKind.Sound) _q.Play(r.Key);
            }
        }

        // ---- Mechanisms --------------------------------------------------------------------------------------------------
        private void ReadLog(MechanismLog log, double now)
        {
            for (int i = 0; i < log.Count; i++)
            {
                MechanismEvent e = log[i];
                if (e.Id.IsNone || !_byId.TryGetValue(e.Id.Value, out Source s)) continue;
                if (e.Kind == MechanismEventKind.State) OnState(s, e.Code);
                else OnEvent(s, e, now);
            }
        }

        private void OnState(Source s, int code)
        {
            switch (s.Kind)
            {
                case Kind.Latch:                                                              // release(), L1678
                    if (code == (int)LatchState.Released) { _q.Play(KClank); _q.Play(KChainRelease); _q.Play(KRattleRelease); }
                    break;
                case Kind.Crank:                                                              // the fifth stroke: the door is open, L1890
                    if (code == (int)CrankState.Done) _q.Play(KDoorOpen);
                    break;
                case Kind.Hatch:                                                              // wound to the serving height, L4917
                    if (code == (int)DoorState.Open) _q.Play(KClunk);
                    break;
            }
        }

        private void OnEvent(Source s, in MechanismEvent e, double now)
        {
            int c = e.Code;
            switch (s.Kind)
            {
                case Kind.Relay:                                                              // the depot's pulse, L8515
                    if (c == (int)PulseEvent.LampLit && e.Index >= 0 && e.Index < 3)
                    {
                        double x = _sim.X;
                        double k = _sim.Region == 4 ? 1 - Smooth.Step((x - RelayFadeFromX) / RelayFadeOver) : 1;
                        if (k > 0.02) _q.Play(KRelay[e.Index], e.Value * k * Math.Max(0.25, 0.8 - Math.Abs(x - RelayX) / 8), RelayX);
                    }
                    break;
                case Kind.Latch:
                    if (c == (int)LatchEvent.Creak) _q.Play(KCreakLatch);                      // f > 20 of the Pull, L1873
                    break;
                case Kind.Shutter:
                    if (c == (int)DoorEvent.Cue) _q.Play(KThud);                              // 560 ms after the release, L1679
                    break;
                case Kind.Crank:
                    if (c == (int)CrankEvent.Stroke) { _q.Play(KRatchet); _q.Play(KDoorRumble); }   // each stroke, L1889
                    break;
                case Kind.Cart:
                {
                    var b = (TippingBridge)s.M;
                    if (c == (int)TippingBridgeEvent.Tip) _q.Play(KScrape, 1, b.X);         // tipOver, L4739
                    else if (c == (int)TippingBridgeEvent.Land) _q.Play(KThud, 1, b.X);     // into the trench, L4757
                    break;
                }
                case Kind.TubeLetter:
                    if (c == (int)TubeLetterEvent.Cough) { _q.Play(KChainTube); _q.PlayAfter(now, TubeTap, KTap); }   // L4772
                    else if (c == (int)TubeLetterEvent.Landed) _q.Play(KSetDownFloor);        // L4779
                    break;
                case Kind.Press:                                                              // the ram lands, near and in region 2 (L7349–L7350)
                    if (c == (int)CrusherEvent.Slam && _sim.Region == 2) { _q.Play(KThud, 1, PressX); _q.Play(KClank, 1, PressX); }
                    break;
                case Kind.Plate:
                    if (c == (int)LoadPlateEvent.Press) _q.Play(KPlate);                       // L2375
                    break;
                case Kind.Gate:
                    if (c == (int)FollowerEvent.Tick) _q.Play(KGateTick, 1, GateX);           // every 5 cm up, L2382
                    else if (c == (int)FollowerEvent.Slam) _q.Play(KGateSlam, Math.Min(1, Math.Abs(e.Value) / 3), GateX);   // L2386
                    break;
                case Kind.Trolley:
                case Kind.Courier:
                case Kind.Drum:
                case Kind.Body:
                {
                    var p = (Pushable)s.M;
                    if (c == (int)PushableEvent.Tip) _q.Play(KScrape, 1, p.X);               // tipOver, L4739
                    else if (c == (int)PushableEvent.Dock && s.Kind == Kind.Drum) _q.Play(KThud, 1, p.X);   // the drum set, L4728
                    break;
                }
                case Kind.Cradle:
                    if (c == (int)CradleEvent.Take && e.Index == 1) _q.Play(KServoCradleDraw); // let go near the bay: drawn in, L4790
                    else if (c == (int)CradleEvent.Seat) { _q.Play(KServoCradleSeat); _q.Play(KClunk); }   // seated, L4805
                    break;
                case Kind.WeighIn:
                    switch (c)
                    {
                        case (int)WeighEvent.Reading:                                         // L4895–L4897
                            if (e.Index == (int)WeighReading.Under) _q.PlayAfter(now, e.Value, KBuzzShort);
                            else if (e.Index == (int)WeighReading.Over) { _q.Play(KClank); _q.PlayAfter(now, e.Value, KAlarmBell); }
                            else if (e.Index == (int)WeighReading.Person) _q.Play(KClick);
                            break;
                        case (int)WeighEvent.Served: _q.Play(KRatchet); _q.Play(KChainServed); break;   // L4899
                        case (int)WeighEvent.Tick: if (_sim.Region == 2) _q.Play(KTick); break;          // the dial's detents, L4904
                        case (int)WeighEvent.Twitch: _q.Play(KRatchet); _q.PlayAfter(now, TwitchClunk, KClunk); break;   // L4909
                    }
                    break;
                case Kind.Scanner:
                    switch (c)
                    {
                        case (int)Dl06ScanEvent.Sweep: _q.Play(KScanSweep, 1, ScannerX); break;           // L2792
                        case (int)Dl06ScanEvent.Answer: if (e.Index >= 0 && e.Index < 3) _q.Play(KAnswer[e.Index], 1, ScannerX); break;   // L2797
                        case (int)Dl06ScanEvent.Read: _q.Play(KChirp); break;                              // L2800
                        case (int)Dl06ScanEvent.Reject: _q.Play(KReject, 1, ScannerX); break;              // L2801
                        case (int)Dl06ScanEvent.Perk: _q.Play(KChirp); break;                              // L2811
                    }
                    break;
                case Kind.StopLever:
                    if (c == (int)PointsLeverEvent.AutoStart) _q.Play(KKlaxon);                       // startBelt, L2822
                    else if (c == (int)PointsLeverEvent.Thrown) _q.Play(e.Index != 0 ? KKlaxon : KBeltStop);   // L2932
                    else if (c == (int)PointsLeverEvent.Clunk) _q.Play(KClunk);
                    break;
                case Kind.Points:
                    if (c == (int)PointsLeverEvent.Thrown) _q.Play(KClack, 1);                         // L2933
                    else if (c == (int)PointsLeverEvent.Clunk) _q.Play(KClunk);                       // stuck while the belt runs, L2924–L2925
                    break;
                case Kind.Line:
                    OnLine(e, now);
                    break;
            }
        }

        private void OnLine(in MechanismEvent e, double now)
        {
            double x = CarrierX(e.Index);
            switch (e.Code)
            {
                case (int)CarrierLineEvent.Spawned: _q.Play(KHatchLift, 1, x); break;                 // L2680
                case (int)CarrierLineEvent.Docked: _q.Play(KBell, 1, x); break;                       // L2701
                case (int)CarrierLineEvent.Junction: _q.Play(KClack, 0.4, x); break;                  // L2709
                case (int)CarrierLineEvent.Tip: _q.Play(KClank, 1, x); break;                         // L2715
                case (int)CarrierLineEvent.Sinking: _q.Play(KClunk, 1, x); _q.Play(KHatchLift, 1, x); break;   // L2716, L2741
                case (int)CarrierLineEvent.PayloadDumped: _q.PlayAfter(now, PayloadTumble, KTumble, 1, x); break;   // L2730
                case (int)CarrierLineEvent.RiderTipped: _q.Play(KWorried); break;                      // tipOut, L2981
            }
        }

        /// <summary>The rail x of the carrier with sequence number <paramref name="seq"/>, or NaN.</summary>
        private double CarrierX(int seq)
        {
            if (_line == null) return double.NaN;
            for (int i = 0; i < _line.Count; i++) if (_line.At(i).Seq == seq) return _line.At(i).Position;
            return double.NaN;
        }

        // ---- The motor ---------------------------------------------------------------------------------------------------
        /// <summary>
        /// The motor's events not read yet: from its step's own when it stepped (the calls' events before them were read
        /// with the last step), else only what calls have added since (a scene act holds him and the list is not cleared).
        /// </summary>
        private void ReadMotor(D17Motor motor, double now)
        {
            var events = motor.Events;
            int from;
            if (motor.StepCount != _motorStep) from = Math.Min(motor.StepEventsStart, events.Count);
            else from = events.Count >= _motorSeen ? _motorSeen : 0;
            _motorStep = motor.StepCount;
            _motorSeen = events.Count;
            for (int i = from; i < events.Count; i++)
            {
                MotorEvent e = events[i];
                switch (e.Kind)
                {
                    case MotorEventKind.Footstep: _q.Play(KStep, e.Value); break;                        // stepSounds, L2073
                    case MotorEventKind.Jump: _q.Play(KJump); break;                                     // L1994
                    case MotorEventKind.Land: _q.Play(KLand, Math.Min(1, 0.5 + Math.Max(0, e.Value))); break;   // L2026
                    case MotorEventKind.Bonk: _q.Play(KBonk); break;                                     // L2017
                    case MotorEventKind.MantleStart:                                                     // startMantle, L1910–L1911
                        _q.Play(KJump);
                        _q.PlayAfter(now, MantleScrape1, KScrape);
                        _q.PlayAfter(now, MantleStrain, KStrain);
                        _q.PlayAfter(now, MantleScrape2, KScrape);
                        _q.PlayAfter(now, MantleClick, KClick);
                        break;
                    case MotorEventKind.ClipChanged: OnClip(e.Name); break;
                    case MotorEventKind.ActEvent: OnActEvent(e.Name); break;
                    case MotorEventKind.PickedUp: _q.Play(KScrape); break;                               // f22: it is in his hands, L4419, L2278
                    case MotorEventKind.SetDown: if (e.Name == "release") _q.Play(KSetDownFloor); break;  // L4425
                    case MotorEventKind.Placed: _q.Play(KSetDownDeck); break;                            // into a carrier, L4452
                    case MotorEventKind.Death: _q.Play(DeathKey(e.Name)); break;                         // die(), L7441
                }
            }
        }

        /// <summary>The sounds the prototype plays where it starts a clip (<c>setClip</c> beside <c>Sound.*</c>).</summary>
        private void OnClip(string clip)
        {
            switch (clip)
            {
                case ClipNames.Grab: _q.Play(KTap); break;                       // the grab, L1852, L4464–L4466
                case "Pull": _q.Play(KCreakPull); break;                         // the latch, L1849
                case "Tug": _q.Play(KServoTug); break;                           // the cord lamp, L1848
                case "LeverPull":
                case "LeverStuck": _q.Play(KServoLever); break;                  // DL-06's levers, L2913
            }
        }

        private void OnActEvent(string name)
        {
            switch (name)
            {
                case "sound": _q.Play(KLift); break;                             // Lift f13, L4418, L2277
                case "takeoff": _q.Play(KJump); break;                           // a hop's take-off, L2891
                case "land": _q.Play(KLand, 0.6); break;                         // and its landing, L2892
                case ClipNames.Flinch: _q.Play(KWorried); break;                 // the latch's Pull → Flinch, L1875
                case "flinch": _q.Play(KWorried); break;                         // stuck in the trench, L4520
            }
        }

        private static string DeathKey(string kind)
        {
            switch (kind)
            {
                case nameof(Motor.DeathKind.Crush): return KDeath[0];
                case nameof(Motor.DeathKind.Shock): return KDeath[1];
                case nameof(Motor.DeathKind.Grabbed): return KDeath[2];
                case nameof(Motor.DeathKind.Fall): return KDeath[3];
                default: return null;
            }
        }

        // ---- Scene acts ----------------------------------------------------------------------------------------------------
        private void ReadSceneAct()
        {
            // A death the motor cannot play (DeathAct: he sinks meanwhile, the sump's way) is a scene act; its phase is the kind.
            ActId kind = _sim.SceneActKind;
            if (kind == ActIds.Death && _lastActKind != ActIds.Death) _q.Play(DeathKey(_sim.SceneActPhase.Name));   // die(), L7441
            _lastActKind = kind;
            ActId phase = kind == Dl06ChuteFallAct.ChuteKind ? _sim.SceneActPhase : ActId.None;
            if (phase == Dl06ChuteFallAct.Down && _lastActPhase != Dl06ChuteFallAct.Down) { _q.Play(KThud); _q.Play(KTumble); }   // onto the heap, L2993
            _lastActPhase = phase;
        }

        // ---- Per-frame polls -------------------------------------------------------------------------------------------------
        private void Poll(double now, double dt, bool calm)
        {
            // The racks light row by row after the reveal, each with its sound (L2414–L2427); none when the reveal was restored.
            RacksLit = 0;
            if (_reveal != null)
            {
                bool lit = _reveal.Revealed && !_reveal.Pending;
                if (_reveal.Time != _rowsFor) { _rowsFor = _reveal.Time; _rowsLit = 0; }
                double rk = lit ? now - _reveal.Time : -1;
                RacksLit = RackRows.Lit(lit, rk, calm);
                for (int i = 0; lit && i < RowTimes.Length; i++)
                    if (rk >= RowTimes[i] && _rowsLit <= i) { _rowsLit = i + 1; if (_reveal.Time > 0) _q.Play(KRowOn[i]); }
            }
            // Wheels squeak at random while they roll (L2350, L4703).
            Squeak(_trolley, TrolleySqueakRate, dt, _trolley != null ? _trolley.Velocity : 0);
            Squeak(_drum, PushSqueakRate, dt, _sim.Motor.Vx);
            // The hatch ratchets as it winds up (L4917).
            if (_hatch != null && _hatch.State == DoorState.Opening && _rng.NextDouble() < dt * HatchRatchetRate) _q.Play(KRatchet);
        }

        private void Squeak(Pushable p, double rate, double dt, double speed)
        {
            if (p == null || !p.Held) return;
            if (Math.Abs(speed) > SqueakAbove && _rng.NextDouble() < dt * rate) _q.Play(KSqueak, 1, p.X);
        }

        /// <summary><c>updateAtmosphere</c>'s sounds (L7895–L7966): the drops, the live cable, distant machinery.</summary>
        private void Atmosphere(double t, double dt, bool voicesHeld)
        {
            bool inPlay = !_sim.Exited;
            double px = _sim.X;
            for (int i = 0; i < DripX.Length; i++)
            {
                _dripT[i] += dt;
                if (_dripFall[i] < 0 && _dripT[i] > _dripEvery[i]) { _dripT[i] = 0; _dripFall[i] = 0; _dripEvery[i] = DripNextMin + _rng.NextDouble() * DripNextSpread; }
                if (_dripFall[i] >= 0)
                {
                    _dripFall[i] += dt;
                    double y = DripY[i] - 0.5 * 9.8 * _dripFall[i] * _dripFall[i];
                    if (y <= 0)
                    {
                        _dripFall[i] = -1;
                        if (inPlay) _q.Play(KDrip, Math.Max(0, 1 - Math.Abs(DripX[i] - px) / DripHear), DripX[i]);   // L7904
                    }
                }
            }
            if (t > _puffUntil && t > _puffNext) { _puffUntil = t + 1.0 + _rng.NextDouble() * 0.9; _puffNext = _puffUntil + 2.5 + _rng.NextDouble() * 4; }   // L7913
            if (t > _nextSpark)                                                                                          // L7938
            {
                SparkUntil = t + SparkFor;
                _nextSpark = t + CrackleMin + _rng.NextDouble() * CrackleSpread;
                _q.Play(KCrackle, Math.Max(CableFloor, 1 - Math.Abs(CableX - px) / CableOver), CableX);
            }
            switch (_atmos.Update(t, inPlay, voicesHeld))                                                                // L7964
            {
                case DistantSound.Distant: _q.Play(KDistant); break;
                case DistantSound.Groan: _q.Play(KGroan); break;
            }
            Puffing = t < _puffUntil;
        }

        /// <summary>The live cable arcs until this clock time (<c>atmos.sparkUntil</c>: 0.18 s from each crackle, L7938), for its light.</summary>
        public double SparkUntil { get; private set; }

        /// <summary>A steam wisp is puffing (<c>atmos.puff</c>, L7913–L7915): the hiss is louder (<see cref="AtmosphereRules.HissLevel"/>).</summary>
        public bool Puffing { get; private set; }

        // ---- Continuous layers -----------------------------------------------------------------------------------------------
        private void SetLoops()
        {
            var sim = _sim;
            int region = sim.Region;
            double x = sim.X;
            bool inPlay = !sim.Exited;
            _loops[(int)SfxLoop.Hum] = inPlay ? 1 : 0;                                                 // startPlay, L8104
            _loops[(int)SfxLoop.Buzz] = inPlay ? WorkBulbBuzz : 0;                                     // applyLights, L1574
            _loops[(int)SfxLoop.Hiss] = AtmosphereRules.SteamHiss(x, inPlay, AtmosphereRules.HissLevel(Puffing));   // L7965
            double roll = 0;
            if (region == 2 && _trolley != null && _trolley.Held) roll = Math.Min(1, Math.Abs(_trolley.Velocity) / TrolleyRollSpeed);   // L2370
            var ride = _line?.Ride;
            if (region == 3 && ride != null) roll = _line.Running && ride.State == CarrierState.Move ? RideRoll : 0;   // updateRide, L2969
            _loops[(int)SfxLoop.Roll] = roll;
            _loops[(int)SfxLoop.Tubes] = region == 2 ? RacksLit * Math.Max(TubesFloor, 1 - Math.Abs(x - TubesX) / TubesOver) : 0;   // L2428
            _loops[(int)SfxLoop.Belt] = region == 3 && _line != null && _line.Running ? Math.Max(BeltFloor, 1 - Math.Abs(x - BeltX) / BeltOver) : 0;   // L2830
            bool dragging = (_courier != null && _courier.Held) || (_body != null && _body.Held);
            _loops[(int)SfxLoop.Drag] = dragging ? Math.Min(1, Math.Abs(sim.Motor.Vx) / DragSpeed) : 0;   // L4703
        }
    }

    /// <summary>The racks' rows lighting after the reveal (<c>ROW_TIMES</c>, L2414–L2427): what the tubes' level and the rack lights read.</summary>
    public static class RackRows
    {
        public const int Count = 6;
        public const double Flicker = 0.6;

        /// <summary>Row <paramref name="i"/>'s brightness <paramref name="rk"/> seconds after the reveal (0 before it): a flicker for 0.6 s, or calm's ease (L2417–L2419).</summary>
        public static double Row(int i, double rk, bool calm)
        {
            double k = rk - ChapterSounds.RowTimes[i];
            if (k < 0) return 0;
            if (calm) return Smooth.Step(k / Flicker);
            return k < Flicker ? (Math.Sin(k * 57 + i * 3.1) > 0.15 ? 1 : 0.1) : 1;
        }

        /// <summary>The mean of the rows (<c>lit</c>, L2423).</summary>
        public static double Lit(bool revealed, double rk, bool calm)
        {
            if (!revealed) return 0;
            double lit = 0;
            for (int i = 0; i < Count; i++) lit += Row(i, rk, calm) / Count;
            return lit;
        }
    }
}
