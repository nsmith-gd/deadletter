using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Water;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl14b;
using DeadLetter.Core.Scenes.Dl16;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// Chapter 1's sounds (region 6, DL-12 to DL-17: index.html's <c>Sound.*</c> calls in <c>updateAtt</c>/<c>updateAtt2</c>/
    /// <c>updateAtt3</c> and their acts, L5288–L6409), for <see cref="ChapterSounds"/> to queue alongside the scenes' own
    /// <c>sound:</c> cues (the strip's plate, the lesson's first bell, the dismissal's bell). Read from the step:
    /// <list type="bullet">
    /// <item>the chapter's mechanisms' events and transitions (<see cref="MechanismGraph.Log"/>), which Core's mechanisms
    /// already raise where the prototype sounds;</item>
    /// <item>the chapter's acts (<see cref="ChapterSim.SceneActKind"/>, its phase and clock): the reach's servo, a lift at f13,
    /// a set-down, the duct's turn, the drawer's drag, the pushes in the servery;</item>
    /// <item>the prototype's random per-frame sounds (<c>Math.random() &lt; dt · k</c>) on the seeded <see cref="AudioRng"/>:
    /// the chain's taps against the pole, the crank's taps, the duct's crawl, the rig's splashes.</item>
    /// </list>
    /// Not here yet: the school's relay boxes (L6318–L6324: their art and state are not in Core), the stamp and the T-key in
    /// DL-17's read (L5705, L5779), the lever's clunk while figures wait (L5691), the stored figures' squeaks (L5753), the
    /// spindle tried without its key (L6212), and every <c>shake()</c> (the camera's, not a sound). Allocation-free per step.
    /// </summary>
    public sealed class AttendanceSounds
    {
        /// <summary>The cue the DL-14a rules raise when the door opens; its three sounds are played here (L6227).</summary>
        public const string DoorCueKey = "door";
        /// <summary>The random rates, per second: taps while the chain grinds (L5453), the duct's crawl (L5642), the crank's taps in DL-14a (L6230), the rig's splashes (L6253).</summary>
        public const double RattleTapRate = 9, CrawlTapRate = 3, WindTapRate = 6, SplashRate = 8;
        /// <summary>DL-14a's crank taps only while he is in its room (x 248–263, L6230).</summary>
        public const double WindTapX0 = 248, WindTapX1 = 263;
        /// <summary>The act frames (24 fps) the prototype sounds at: a lift's f13 (L5328), a set-down's f14 (L6060), the pole leaving its jam f16 (L5327).</summary>
        public const double LiftFrame = 13, SetDownFrame = 14, UnjamFrame = 16;

        private enum Kind
        {
            None, Strip, Gate12, Lesson, Brake, Crank, Blinds, Lift15, Seats, Rack16, Latch16, RackCw, Car, Sluice, Rig, FloatLatch,
            StairDoor, RestDoor, Trolley,
        }

        private static readonly KeyValuePair<string, Kind>[] Ids =
        {
            P("dl12.strip", Kind.Strip), P("dl12.gate", Kind.Gate12), P("dl13.lesson", Kind.Lesson), P("dl13.brake", Kind.Brake),
            P("dl14.crank", Kind.Crank), P("dl14.blinds", Kind.Blinds), P("dl14a.brake", Kind.Brake), P("dl14a.crank", Kind.Crank),
            P("dl14a.door", Kind.RestDoor), P("dl14b.trolley", Kind.Trolley), P("dl15.lift", Kind.Lift15), P("dl15.seats", Kind.Seats),
            P("dl16.rack", Kind.Rack16), P("dl16.latch", Kind.Latch16), P("dl16.rackCW", Kind.RackCw), P("dl16a.car", Kind.Car),
            P("dl17.sluiceA", Kind.Sluice), P("dl17.sluiceB", Kind.Sluice), P("dl17.sluiceC", Kind.Sluice), P("dl17.rig", Kind.Rig),
            P("dl17.latch", Kind.FloatLatch), P("dl17.stairDoor", Kind.StairDoor),
        };

        private static KeyValuePair<string, Kind> P(string id, Kind k) => new KeyValuePair<string, Kind>(id, k);

        private static readonly string KBuzzShort = SfxKeys.Simple["buzzShort"], KBell = SfxKeys.Simple["bell"], KGateSlam = SfxKeys.Simple["gateSlam"],
            KClack = SfxKeys.Simple["clack"], KThud = SfxKeys.Simple["thud"], KPawlClick = SfxKeys.Simple["pawlClick"], KClunk = SfxKeys.Simple["clunk"],
            KGroan = SfxKeys.Simple["groan"], KRatchet = SfxKeys.Simple["ratchet"], KScrape = SfxKeys.Simple["scrape"], KStrain = SfxKeys.Simple["strain"],
            KTap = SfxKeys.Simple["tap"], KClank = SfxKeys.Simple["clank"], KPlate = SfxKeys.Simple["plate"], KSqueak = SfxKeys.Simple["squeak"],
            KDoorOpen = SfxKeys.Simple["doorOpen"], KLift = SfxKeys.Simple["lift"], KClick = SfxKeys.Simple["click"], KWorried = SfxKeys.Simple["worried"],
            KSplash = SfxKeys.Simple["splash"], KSetDownFloor = SfxKeys.SetDown(false),
            KChainWind = SfxKeys.Chain(2.2), KChainLatch = SfxKeys.Chain(2.5), KChainCall = SfxKeys.Chain(3.0), KChainBell = SfxKeys.Chain(2.0),
            KChainShoot = SfxKeys.Chain(1.0), KCreakPeel = SfxKeys.Creak(0.5), KCreakDoor = SfxKeys.Creak(0.7), KCreakFloat = SfxKeys.Creak(0.6),
            KCreakHook = SfxKeys.Creak(0.4), KServoReach = SfxKeys.Servo(0.25, 500, 820), KServoDuct = SfxKeys.Servo(0.3, 300, 500),
            KServoTurn = SfxKeys.Servo(0.3, 300, 420);

        private readonly ChapterSim _sim;
        private readonly SfxQueue _q;
        private readonly AudioRng _rng;
        private readonly Dictionary<string, Kind> _byId = new Dictionary<string, Kind>(StringComparer.Ordinal);
        private readonly PairedBlindDrive _blinds14;
        private readonly WindCrank _crank14a;
        private readonly SluiceRig _rig;
        private readonly Dl16Bridge _bridge;
        private readonly Dl14bFigure _figure14b;
        private readonly CarriedItem _bag;
        // The act being read: its kind and phase, its clock last step, whether it began this step.
        private string _actKind, _actPhase;
        private double _actT;
        private bool _poleWasJammed;
        private double _bridgeWas = double.NaN, _figureOutWas = double.NaN;
        private Dl14bFigureState _figureWas;

        public AttendanceSounds(ChapterSim sim, SfxQueue queue, AudioRng rng)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            _q = queue ?? throw new ArgumentNullException(nameof(queue));
            _rng = rng ?? throw new ArgumentNullException(nameof(rng));
            foreach (var p in Ids) _byId[p.Key] = p.Value;
            sim.Graph.TryGet("dl14.blinds", out _blinds14);
            sim.Graph.TryGet("dl14a.crank", out _crank14a);
            sim.Graph.TryGet("dl17.rig", out _rig);
            sim.Graph.TryGet("dl16.bridge", out _bridge);
            sim.Graph.TryGet("dl14b.figure", out _figure14b);
            sim.Graph.TryGet("dl14a.bag", out _bag);
        }

        /// <summary>The drawer's drag layer (<c>Sound.drag(0.6)</c> while it slides, <c>drag(0)</c> after, L5696–L5697).</summary>
        public double Drag { get; private set; }

        /// <summary>A <c>sound:</c> cue key this reader plays itself (DL-14a's door: clank, bell and the door, not one file).</summary>
        public static bool OwnsCue(string key) => key == DoorCueKey;

        /// <summary>A new world: no act carries over, the polled states start again.</summary>
        public void OnPlaced()
        {
            _actKind = _actPhase = null;
            _actT = 0;
            _bridgeWas = _figureOutWas = double.NaN;
            Drag = 0;
        }

        /// <summary>After each step (from <see cref="ChapterSounds.Step"/>, with its clock and dt).</summary>
        public void Step(double now, double dt)
        {
            ReadLog(_sim.Graph.Log, now);
            ReadAct();
            Poll(dt);
        }

        // ---- Mechanisms ---------------------------------------------------------------------------------------------------
        private void ReadLog(MechanismLog log, double now)
        {
            for (int i = 0; i < log.Count; i++)
            {
                MechanismEvent e = log[i];
                if (e.Id.IsNone || !_byId.TryGetValue(e.Id.Value, out Kind k)) continue;
                if (e.Kind == MechanismEventKind.State) OnState(k, e.Code);
                else OnEvent(k, e, now);
            }
        }

        private void OnState(Kind k, int code)
        {
            switch (k)
            {
                case Kind.Brake:                                                              // the brake toggles; braked, the frame groans (L5352–L5354, L6079)
                    _q.Play(KPawlClick);
                    if (code == (int)CycleBrakeState.Braked) _q.Play(KGroan);
                    break;
                case Kind.Latch16:                                                            // the rack latched (L5764)
                    if (code == (int)LatchState.Released) { _q.Play(KClank); _q.Play(KChainLatch); }
                    break;
                case Kind.StairDoor:                                                          // DL-17's stair door starts to open (L5789)
                    if (code == (int)DoorState.Opening) _q.Play(KCreakDoor);
                    break;
                case Kind.RestDoor:                                                           // dark long enough: the door opens (L6227)
                    if (code == (int)DoorState.Opening) { _q.Play(KClank); _q.Play(KBell); _q.Play(KDoorOpen); }
                    break;
                case Kind.Car:                                                                // what the push sent the car to do (L6146, L6173–L6176)
                    if (code == (int)DumbwaiterState.Down) _q.Play(_sim.Act != null && _sim.Act.Kind.Name == "dl16a.callPush" ? KChainCall : KChainBell);
                    else if (code == (int)DumbwaiterState.Shoot) _q.Play(KChainShoot);
                    else if (code == (int)DumbwaiterState.Rise) { _q.Play(KClunk); _q.Play(KChainCall); }
                    break;
            }
        }

        private void OnEvent(Kind k, in MechanismEvent e, double now)
        {
            int c = e.Code;
            switch (k)
            {
                case Kind.Strip:
                    if (c == (int)PresenceEvent.AskForCoat) _q.Play(KBuzzShort);              // L5390
                    else if (c == (int)PresenceEvent.Thanks) _q.Play(KBell);                  // L5393
                    break;
                case Kind.Gate12:
                    if (c == (int)FollowerEvent.Slam) _q.Play(KGateSlam, 0.8, Dl12Lane.GateX);  // L5404
                    break;
                case Kind.Lesson:
                    if (c == (int)CycleClockEvent.Lap) _q.Play(KBell);                        // each lap from the first step (L5421)
                    else if (c == (int)CycleClockEvent.TrackUp && e.Index < 3) _q.Play(KClack);    // a step clacks out (L5425)
                    else if (c == (int)CycleClockEvent.TrackDown && e.Index < 3) _q.Play(KThud);   // and thuds home
                    break;
                case Kind.Brake:
                    if (c == (int)CycleBrakeEvent.Clunk) { _q.Play(KPawlClick); _q.Play(KClunk); }   // nothing to hold (L5346)
                    break;
                case Kind.Crank:
                    if (c == (int)WindCrankEvent.Wind) { _q.Play(KChainWind); _q.Play(KRatchet); }   // L5372, L6092
                    else if (c == (int)WindCrankEvent.Ratchet) _q.Play(KRatchet);                     // L5374, L6094
                    break;
                case Kind.Blinds:
                    if (c == (int)PairedBlindEvent.Grind) { _q.Play(KScrape); if (_rng.NextDouble() < 0.4) _q.Play(KStrain); }   // L5460
                    else if (c == (int)PairedBlindEvent.Peel) _q.Play(KCreakPeel);                                        // L5474
                    break;
                case Kind.Trolley:
                    switch (c)
                    {
                        case (int)EscortEvent.Squeak: _q.Play(KSqueak); break;                                  // L6376, L6386
                        case (int)EscortEvent.Turned: _q.Play(KServoTurn); break;                               // L6378
                        case (int)EscortEvent.FigureKept: _q.Play(KBell); break;                                // L6387
                        case (int)EscortEvent.CaughtHim:
                        case (int)EscortEvent.FigureSeen: _q.Play(KBell); _q.PlayAfter(now, 0.26, KBell); break;   // L6396, L6405
                    }
                    break;
                case Kind.Lift15:
                    if (c == (int)PupilLiftEvent.Buzz) _q.Play(KBuzzShort);                   // L5716
                    else if (c == (int)PupilLiftEvent.Arrive) _q.Play(KClunk);                // L5722
                    else if (c == (int)PupilLiftEvent.Ratchet) _q.Play(KRatchet);
                    break;
                case Kind.Seats:
                    if (c == (int)SeatRowEvent.Lamp) _q.Play(KPlate);                         // L5728
                    else if (c == (int)SeatRowEvent.Bell) _q.PlayAfter(now, e.Value, KBell);   // the second bell (the first is the rules' cue), L5732
                    break;
                case Kind.Rack16:
                    if (c == (int)RackEvent.Stored) _q.Play(KRatchet);                        // L5757
                    break;
                case Kind.RackCw:
                    if (c == (int)CounterweightRackEvent.Ratchet) _q.Play(KRatchet);          // L5766
                    break;
                case Kind.Car:
                    if (c == (int)DumbwaiterEvent.Over) _q.Play(KBuzzShort);                  // L6174
                    else if (c == (int)DumbwaiterEvent.CatchBite) { _q.Play(KClank); _q.Play(KRatchet); }   // L6242
                    else if (c == (int)DumbwaiterEvent.Arrive) _q.Play(KClunk);               // L6236, L6237, L6244
                    break;
                case Kind.Sluice:
                    if (c == (int)SluiceEvent.Clunk) { _q.Play(KPawlClick); _q.Play(KClunk); }   // L6194
                    break;
                case Kind.Rig:
                    if (c == (int)SluiceRigEvent.Started) { _q.Play(KRatchet); _q.Play(KSplash, 0.5); }   // L6205
                    else if (c == (int)SluiceRigEvent.RefusedLow) { _q.Play(KClunk); _q.Play(KWorried); }   // L6203
                    else if (c == (int)SluiceRigEvent.RefusedShut) { _q.Play(KClunk); _q.Play(KGroan); }    // L6204
                    break;
                case Kind.FloatLatch:
                    if (c == (int)FloatLatchEvent.Clank) { _q.Play(KClank); _q.Play(KCreakFloat); }   // L6258
                    break;
            }
        }

        // ---- Acts ---------------------------------------------------------------------------------------------------------
        private void ReadAct()
        {
            var act = _sim.Act;
            string kind = act != null ? act.Kind.Name : null, phase = act != null ? act.Phase.Name : null;
            double t = act != null ? act.T : 0;
            bool began = kind != _actKind || phase != _actPhase;
            double was = began ? -1 : _actT;
            if (kind != _actKind) _poleWasJammed = _blinds14 != null && _blinds14.Held;
            _actKind = kind; _actPhase = phase; _actT = t;
            if (kind == null) { Drag = 0; return; }

            switch (phase)
            {
                case "Lift":                                                                  // f13 (L5328, L5668, L6101, L6139)
                    if (Crossed(was, t, LiftFrame / 24))
                    {
                        _q.Play(KLift);
                        if (kind == "dl14a.basket") _q.Play(KStrain);                         // the bag is heavy (L6100)
                    }
                    if (kind == "dl14.pole" && _poleWasJammed && Crossed(was, t, UnjamFrame / 24)) _q.Play(KClank);   // L5327
                    break;
                case "SetDownHigh":
                    if (!Crossed(was, t, SetDownFrame / 24)) break;
                    if (kind == "dl12.peg") { _q.Play(KSetDownFloor); _q.Play(KTap); }                        // on the peg (L5337)
                    else if (kind == "dl14a.hook")                                                            // on the cord's hook (L6047–L6049)
                    {
                        _q.Play(KTap); _q.Play(KCreakHook);
                        if (_bag != null && _bag.State == ItemState.Carried) _q.Play(KThud);
                    }
                    else if (kind == "dl14a.wallPeg") { _q.Play(KSetDownFloor); _q.Play(KTap); }              // L6060
                    break;
                case "SetDown":
                    if (kind == "dl14.wheel" && Crossed(was, t, SetDownFrame / 24)) { _q.Play(KClank); _q.Play(KRatchet); }   // back into the jam (L5338)
                    break;
                case "Present":
                    if (began && (kind == "dl12.reachPeg" || kind == "dl14a.reachHook")) _q.Play(KServoReach);   // L5307, L6072
                    break;
                case "Along":
                    if (began && kind == "dl14.hatch") _q.Play(KServoDuct);                   // he turns along the duct (L5638)
                    break;
                case "Clip":
                    if (began && kind == "dl15.chair") _q.Play(KTap);                         // sat in Mara's place (L5659)
                    break;
                case "Nudge":
                    if (kind == "dl14b.figure" && Crossed(was, t, 0.6)) { _q.Play(KSqueak); _q.Play(KTap); }   // L6107
                    break;
                case "PressButtonHigh":                                                       // the servery's push (t > 0.45) and the car's bell (t > 0.55), L6146, L6170
                    if (Crossed(was, t, kind == "dl16a.callPush" ? 0.45 : 0.55)) { _q.Play(KClick); _q.Play(KBell); }
                    break;
            }
            Drag = kind == "dl17.drawer" && phase == "Tug" && t > 0.35 && t <= 1.6 ? 0.6 : 0;   // L5696–L5697
        }

        /// <summary>The act's clock passed <paramref name="at"/> this step (a new act or phase starts below everything).</summary>
        private static bool Crossed(double was, double now, double at) => was < at && now >= at;

        // ---- The prototype's per-frame polls ----------------------------------------------------------------------------
        private void Poll(double dt)
        {
            var sim = _sim;
            if (_blinds14 != null && _blinds14.Slipping && _rng.NextDouble() < dt * RattleTapRate) _q.Play(KTap);       // L5453
            if (_actKind == "dl14.hatch" && _actPhase == "Along" && _rng.NextDouble() < dt * CrawlTapRate) _q.Play(KTap);   // L5642
            if (_crank14a != null && _crank14a.State == WindCrankState.Winding && sim.Region == 6 && sim.X > WindTapX0 && sim.X < WindTapX1
                && _rng.NextDouble() < dt * WindTapRate) _q.Play(KTap);                                                   // L6230
            if (_rig != null && _rig.Engaged && _rng.NextDouble() < dt * SplashRate) _q.Play(KSplash, 0.15);           // L6253
            if (_bridge != null)
            {
                double b = _bridge.Position;                                                   // it lands at 0 or 1: clunk (L5743)
                if (!double.IsNaN(_bridgeWas) && b != _bridgeWas && (b == 0 || b == 1)) _q.Play(KClunk);
                _bridgeWas = b;
            }
            if (_figure14b != null)
            {
                double o = _figure14b.Out;                                                     // out of the bay: clunk; coasted to a stop: tap (L6363–L6364)
                if (!double.IsNaN(_figureOutWas) && _figureOutWas < 1 && o >= 1) _q.Play(KClunk);
                if (!double.IsNaN(_figureOutWas) && _figureWas == Dl14bFigureState.Rolling && _figure14b.State == Dl14bFigureState.Free) _q.Play(KTap);
                _figureOutWas = o;
                _figureWas = _figure14b.State;
            }
        }
    }
}
