using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;

namespace DeadLetter.Core.Scenes.Dl09
{
    /// <summary>
    /// DL-09 The Slipping Cage (port_architecture §5; docs/scenes/DL-09_the_slipping_cage.md §1–9 and its passes): off the top
    /// of DL-08's returns belt, three climbs to the upper landing (<c>cage</c>); the two plates into the counterweight's tray
    /// (short of two, the cage dips under him and hauls back); the cage: it settles, lets down, shudders, slips, catches once
    /// 0.35 above the lit landing and slips again; Use throws its pawl, which bites from 0.45 above the landing to 0.06 below
    /// it and eases the cage onto the landing (too early it rattles, too late it hits the buffers in its sump: a death); off
    /// onto the landing (<c>landing8</c>), through the antechamber under the downed cable's two arcs (the first touch ever
    /// knocks him back, any other kills him), into the tunnel (<c>tunnel</c>), the long hopscotch, the city from the balcony
    /// (<c>awe</c>, the <c>refuge</c> moment), the slow walk on and his label, to DL-10 at <c>UPONLY.x0</c>. Region 4, from
    /// <c>CG.x0</c>; lines are index.html at 7b3c123.
    /// <para><b>After DL-08.</b> DL-09 does not start its region: DL-08 does (the chapter lists it first in region 4), and its
    /// def owns region 4's way in and back (the doorway at <c>REGION4_X</c>, DL-07's rules switch him to region 4), its belt,
    /// platform and pawl. DL-09 reads nothing of DL-08's: the deck is <c>GALLERY.h</c> wherever he is in region 4
    /// (<c>game.upper</c> holds from <c>landing</c> to <c>school</c>), the left wall is DL-08's and outside DL-09's stretch. The
    /// checkpoints DL-09 reaches are its rows of the table: <c>cage</c>, <c>landing8</c> and <c>tunnel</c> (the last also from
    /// DL-08's <c>goods</c> and <c>latched</c>, L3421).</para>
    /// <para>Not ported here: the den (a secret, §4.27) and the coin viewer (a curio), the hopscotch replayed as a curio
    /// (Use on the chalk once played), the tannoy <c>tan_bridge</c> and the camera's framings (presentation).</para>
    /// </summary>
    public static class Dl09Scene
    {
        public const string Id = "DL-09";
        public const int Region = Dl09Lane.Region;

        /// <summary>Its checkpoints (<see cref="ChapterDefs.PrologueCheckpoints"/>).</summary>
        public const string CageCheckpoint = "cage", Landing8Checkpoint = "landing8", TunnelCheckpoint = "tunnel";
        /// <summary><c>cage</c>: on the upper landing within 0.9 of the shaft, above <c>CG.top − 0.05</c> (L4949).</summary>
        public const double CageFrom = Dl09Lane.ShaftX0 - 0.9, CageAbove = Dl09Lane.Top - 0.05;
        /// <summary><c>landing8</c>: past the shaft by 0.3, within 0.1 of the landing, the cage caught (L4950).</summary>
        public const double Landing8From = Dl09Lane.ShaftX1 + 0.3, Landing8Within = 0.1;
        /// <summary><c>tunnel</c>: past <c>TUNNEL_X0 + 0.25</c> (L3017, L3421).</summary>
        public const double TunnelFrom = Dl09Lane.TunnelX0 + 0.25;
        /// <summary><c>HOP4_X</c> (L3017): the chalk court; he plays it walking right within 0.5 past it (L3426).</summary>
        public const double HopX = Dl09Lane.Off4 + 66.3, HopWithin = 0.5;
        /// <summary><c>VISTA_X0</c>, <c>AWE_X</c>, <c>EXIT4_X</c> (L3018): the city's stop, and the slow walk after it (<c>paceSlow</c>, L2081).</summary>
        public const double VistaX0 = Dl09Lane.Off4 + 70.0, AweX = Dl09Lane.Off4 + 71.3, Exit4X = Dl09Lane.Off4 + 74.55, SlowFrom = VistaX0 - 0.4;
        /// <summary><c>SLOW_WALK</c> (L327).</summary>
        public const double SlowWalk = 0.39;
        /// <summary>His label (<c>label9</c>): once awed, past <c>AWE_X + 1.6</c> and short of DL-10 (L4942).</summary>
        public const double LabelX0 = AweX + 1.6, LabelX1 = Dl09Lane.X1;
        /// <summary><c>CG.braceX</c> (L3900): in the cage he eases to it at <c>min(1, dt · 3)</c> (L5082).</summary>
        public const double BraceX = Dl09Lane.Off3 + 68.52, BraceRate = 3;

        /// <summary>The once-only beats (the prototype's <c>seen</c>, L1310): the hopscotch, the city, the label.</summary>
        public const string SeenHopscotch = "hopscotch", SeenAwe = "awe", SeenLabel = "label9";

        public static readonly CueId Shake = CueId.Of("shake"), MomentRefuge = CueId.Of("moment:refuge");
        /// <summary>Shakes × 100: the dip 0.5 and its bang 0.4 (L5022, L5025), the shudder 0.35 (L5037), the catch 0.45 (L5041), the bite 0.5 (L5089), the crash 0.9 (L5043).</summary>
        public const int DipShake = 50, DipBangShake = 40, ShudderShake = 35, StallShake = 45, BiteShake = 50, CrashShake = 90;

        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Slipping Cage",
            X0 = Dl09Lane.X0, X1 = Dl09Lane.X1,                                                          // sceneName, L8142
            Region = Region,
            Mechanisms = Mechanisms(),
            Lane = Dl09Lane.Table,
            LaneContributors = Dl09Lane.Contributors,
            Interactables = TrayLoader,
            Rules = () => new SlippingCage09(),
        };

        /// <summary>
        /// In the prototype's order: the plates (moved by the act at #4, so they come first), the counterweight's tray
        /// (<c>loaded</c>, L5016), the pawl, then the cage (<c>updateCage</c> in <c>updateCh1</c>, #7; the pawl first so the cage
        /// sees a bite this step, L5089); the cable's arcs in <c>updateHazards</c>, after it.
        /// </summary>
        public static MechanismDef[] Mechanisms() => new[]
        {
            new MechanismDef("dl09.plate0", () => new CarriedItem("dl09.plate0", PlateParams(0))),
            new MechanismDef("dl09.plate1", () => new CarriedItem("dl09.plate1", PlateParams(1))),
            new MechanismDef("dl09.tray", () => new LoadPlate("dl09.tray", LoadPlateParams.Dl09Tray())),
            new MechanismDef("dl09.cagePawl", () => new CageCatch("dl09.cagePawl", CageCatchParams.Dl09CagePawl())),
            new MechanismDef("dl09.cage", () => new SlippingCage("dl09.cage", SlippingCageParams.Dl09Cage())),
            new MechanismDef("dl09.arc1", () => new LiveArc("dl09.arc1", LiveArcParams.Dl09Arc1())),
            new MechanismDef("dl09.arc2", () => new LiveArc("dl09.arc2", LiveArcParams.Dl09Arc2())),
        };

        /// <summary><c>CW8.plates</c> (L7320): 100.55 and 100.95 on the upper landing.</summary>
        public static readonly double[] PlateX = { Dl09Lane.Off3 + 67.55, Dl09Lane.Off3 + 67.95 };

        /// <summary>
        /// A counterweight plate (<c>itemsHere</c>, L4264: h 0.21, r 0.05, <c>BAIL_BELOW_WRIST</c>; standable within 0.06 where it
        /// lies level, <see cref="PlateLane"/>): on the upper landing at <c>CW8.plates[i]</c>, or in the tray, seat <c>i</c>, past
        /// <c>landing8</c> or, once both have been set in (<c>persist.cw</c>), past <c>cage</c> (<c>resetCh1</c>, L4109).
        /// </summary>
        public static CarriedItemParams PlateParams(int i) => new CarriedItemParams
        {
            HomeX = PlateX[i], HomeBaseY = Dl09Lane.Top,                                                  // base: CG.top
            Radius = 0.05, Half = PlateLane.Reach, Height = PlateLane.Height, BelowWrist = 0.28,           // L4264, BAIL_BELOW_WRIST L320
            MovedAfter = Landing8Checkpoint, MovedState = ItemState.Placed, MovedX = PlateX[i], MovedBaseY = Dl09Lane.Top, MovedSlot = i,
            MovedWithFlag = StoryFlags.CounterweightsStowed, MovedWithFlagAfter = CageCheckpoint,
        };

        public static IInteractable[] TrayLoader(MechanismGraph g) => new IInteractable[]
        {
            new Dl09TrayLoader(g.Get<CarriedItem>("dl09.plate0"), g.Get<CarriedItem>("dl09.plate1"), g.Get<SlippingCage>("dl09.cage")),
        };
    }

    /// <summary>
    /// DL-09's rules: the cage act (<see cref="Dl09CageAct"/>, started and ended as <c>updateCage</c> does, L5022, L5029–L5033,
    /// L5044, L5050), its shakes, <c>persist.cw</c> once both plates are in (L4436) and <c>persist.cageDanger</c> (L5037, L5046);
    /// the checkpoints <c>cage</c> and <c>landing8</c> (L4949–L4950) and <c>tunnel</c> (L3421); the cable's arcs (the first touch
    /// ever knocks him back, any other kills him, L7412–L7413); the region-4 triggers past the antechamber
    /// (<c>updateTriggers4</c>, L3415–L3437: the long hopscotch, the city and its <c>refuge</c> moment); the slow walk on from the
    /// city (<c>paceSlow</c>, L2081) and his label (L4942).
    /// <para>Its hooks run while DL-09 holds him; what they guard by region and x is DL-09's stretch.</para>
    /// </summary>
    public sealed class SlippingCage09 : SceneRules
    {
        private SlippingCage _cage;
        private CarriedItem _p0, _p1;
        private LiveArc _arc1, _arc2;
        private Dl09CageAct _ride;
        private bool _hopped, _awed, _tunnel, _cw;
        private int _shocked;

        public SlippingCage Cage => _cage;
        public CageCatch Pawl { get; private set; }
        public LoadPlate Tray { get; private set; }
        public CarriedItem Plate0 => _p0;
        public CarriedItem Plate1 => _p1;
        public LiveArc Arc1 => _arc1;
        public LiveArc Arc2 => _arc2;
        /// <summary>The <c>refuge</c> moment's clock and state (<c>startMoment('refuge')</c>; the runtime schedules its cue).</summary>
        public MomentDirector Moment { get; } = new MomentDirector(null);
        /// <summary><c>game.dl4.hopped</c>, <c>game.dl4.awed</c> (L3426, L3431; per life, L8047).</summary>
        public bool Hopped => _hopped;
        public bool Awed => _awed;
        /// <summary>Touches of a live arc this life (<c>s.shocked</c>, L7412; <c>resetCh1</c>, L4110).</summary>
        public int Shocked => _shocked;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _cage = g.Get<SlippingCage>("dl09.cage");
            Pawl = g.Get<CageCatch>("dl09.cagePawl");
            Tray = g.Get<LoadPlate>("dl09.tray");
            _p0 = g.Get<CarriedItem>("dl09.plate0"); _p1 = g.Get<CarriedItem>("dl09.plate1");
            _arc1 = g.Get<LiveArc>("dl09.arc1"); _arc2 = g.Get<LiveArc>("dl09.arc2");
            Func<double> clock = () => sim.Clock;                                                           // game.clock % ARC_PERIOD
            _arc1.BindClock(clock); _arc2.BindClock(clock);
            Moment.End();                                                                                   // resetWorld: Music.endMoment(), L8017
            _ride = null;
            _hopped = _tunnel = false;
            _awed = sim.Def.Checkpoints.TryGet(checkpoint, out var cp) && cp.X > Dl09Scene.AweX;          // dl4.awed: c.x > AWE_X (L8047)
            _shocked = 0;                                                                                   // resetCh1, L4110
            _cw = sim.Checkpoints.Flags.Has(StoryFlags.CounterweightsStowed);
        }

        /// <summary><c>paceSlow</c> (L2081): from the city on, he walks slowly to the balcony's end.</summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            bool slow = sim.Region == Dl09Scene.Region && _awed && sim.X > Dl09Scene.SlowFrom && sim.X < Dl09Scene.Exit4X;
            if (slow) sim.Motor.SlowWalkLimit = Dl09Scene.SlowWalk;
        }

        /// <summary>
        /// #4's tail, free movement on the ground (<c>updateTriggers4</c>, L3415–L3437): <c>tunnel</c> (reached at the step's end),
        /// the long hopscotch walking right past the chalk (once ever), and the city past <c>AWE_X</c> (once per life; the act and
        /// the moment once ever, else he walks on).
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            var m = sim.Motor;
            if (!freeStep || sim.Region != Dl09Scene.Region || !m.Grounded) return;
            double x = sim.X;
            if (x > Dl09Scene.TunnelFrom) _tunnel = true;                                                   // L3421
            if (x > Dl09Scene.HopX && x < Dl09Scene.HopX + Dl09Scene.HopWithin && !_hopped && m.Facing > 0)
            {
                _hopped = true;
                if (!sim.Checkpoints.HasSeen(Dl09Scene.SeenHopscotch))                                    // once('hopscotch')
                {
                    sim.Checkpoints.MarkSeen(Dl09Scene.SeenHopscotch);
                    m.Stop();
                    sim.StartAct(new Dl09HopscotchAct(sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config));          // startHopscotch, L3437
                    return;
                }
            }
            if (x > Dl09Scene.AweX && !_awed)
            {
                _awed = true;
                if (!sim.Checkpoints.HasSeen(Dl09Scene.SeenAwe))                                          // once('awe')
                {
                    sim.Checkpoints.MarkSeen(Dl09Scene.SeenAwe);
                    m.Stop();
                    Moment.Start(PrologueMoments.Refuge, sim.Clock, musicAvailable: false);                // startMoment('refuge')
                    sim.Cue(Dl09Scene.MomentRefuge);
                    sim.StartAct(new Dl09AweAct(Moment, sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config));
                }
            }
        }

        /// <summary>
        /// After the mechanisms (#6–#7, <c>updateCage</c> then the checkpoints and the label in <c>updateCh1</c>, then the arcs in
        /// <c>updateHazards</c>).
        /// </summary>
        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            var cid = _cage.Id;
            for (int i = 0; i < log.Count; i++)
            {
                var e = log[i];
                if (e.Id != cid) continue;
                if (e.Kind == MechanismEventKind.State)
                {
                    var s = (SlippingCageState)e.Code;
                    if (s == SlippingCageState.Shudder) { sim.Cue(Dl09Scene.Shake, Dl09Scene.ShudderShake); sim.Checkpoints.SetFlag(StoryFlags.CageDanger, true); }   // L5037
                    else if (s == SlippingCageState.Stall) sim.Cue(Dl09Scene.Shake, Dl09Scene.StallShake);                                                        // L5041
                    else if (s == SlippingCageState.Crash) sim.Cue(Dl09Scene.Shake, Dl09Scene.CrashShake);                                                        // L5043
                    else if (s == SlippingCageState.Caught) sim.Checkpoints.SetFlag(StoryFlags.CageDanger, false);                                                // L5046
                    else if (s == SlippingCageState.Bite) sim.Cue(Dl09Scene.Shake, Dl09Scene.BiteShake);                                                          // L5089
                    continue;
                }
                switch ((SlippingCageEvent)e.Code)
                {
                    case SlippingCageEvent.RideStart:                                                       // game.act = { kind: 'cage' }; game.vx = 0
                        if (e.Index == 0) sim.Cue(Dl09Scene.Shake, Dl09Scene.DipShake);                    // L5022
                        sim.Motor.Stop();
                        _ride = new Dl09CageAct(_cage, sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config);
                        sim.StartAct(_ride);
                        break;
                    case SlippingCageEvent.DipBang: sim.Cue(Dl09Scene.Shake, Dl09Scene.DipBangShake); break;   // L5025
                    case SlippingCageEvent.RideEnd:
                        if (e.Index == SlippingCage.QuirkProud) break;                                     // the act ended itself at #4 (L5094)
                        EndRide(sim);                                                                       // hauled back to the top (L5029, L5050)
                        if (e.Index == SlippingCage.QuirkStartle) SceneQuirk.Start(sim, ClipNames.Startle, cancel: true);
                        break;
                    case SlippingCageEvent.Death:                                                           // into the buffers: die('fall'), L5044
                        EndRide(sim, _cage.Y);
                        sim.Die(DeathKind.Fall);
                        break;
                }
            }
            _ride = sim.Act as Dl09CageAct;

            // updateCh1 (#7): the checkpoints (L4949–L4950).
            if (sim.Region == Dl09Scene.Region)
            {
                double x = sim.X, y = sim.Y;
                if (x > Dl09Scene.CageFrom && x < Dl09Lane.ShaftX0 && y > Dl09Scene.CageAbove) sim.Checkpoints.Reach(Dl09Scene.CageCheckpoint);
                if (x > Dl09Scene.Landing8From && Math.Abs(y - Dl09Lane.Deck) < Dl09Scene.Landing8Within && _cage.State == SlippingCageState.Caught)
                    sim.Checkpoints.Reach(Dl09Scene.Landing8Checkpoint);
            }
            if (_tunnel)                                                                                    // L3421, reached at the step's end
            {
                _tunnel = false;
                string cp = sim.Checkpoints.Current.Name;
                if (cp == "goods" || cp == "latched" || cp == Dl09Scene.CageCheckpoint || cp == Dl09Scene.Landing8Checkpoint)
                    sim.Checkpoints.Reach(Dl09Scene.TunnelCheckpoint);
            }
            // Both plates in the tray: persist.cw = 2 (L4436).
            if (!_cw && _p0.State == ItemState.Placed && _p1.State == ItemState.Placed)
            {
                _cw = true;
                sim.Checkpoints.SetFlag(StoryFlags.CounterweightsStowed, true);
            }
            // His label, once awed (L4940–L4944).
            if (sim.Region == Dl09Scene.Region && _awed && sim.X > Dl09Scene.LabelX0 && sim.X < Dl09Scene.LabelX1
                && !sim.Checkpoints.HasSeen(Dl09Scene.SeenLabel) && SceneQuirk.CanStart(sim))
            {
                sim.Checkpoints.MarkSeen(Dl09Scene.SeenLabel);
                SceneQuirk.Start(sim, ClipNames.CheckLabel, cancel: true);
            }
            // updateHazards: the cable's arcs (L7412–L7413).
            Touch(sim, log, _arc1);
            Touch(sim, log, _arc2);
        }

        /// <summary>The cage act ends at #7 (hauled back up, or the buffers): he stands where it held him.</summary>
        private void EndRide(ChapterSim sim, double y = double.NaN)
        {
            var act = sim.Act as Dl09CageAct;
            if (act == null) return;
            sim.EndAct();
            sim.Motor.Place(act.X, double.IsNaN(y) ? act.Y : y, 1, act.Yaw);
        }

        private void Touch(ChapterSim sim, MechanismLog log, LiveArc arc)
        {
            if (!log.Has(arc.Id, MechanismEventKind.Event, (int)LiveArcEvent.Touch)) return;
            bool alive = !sim.Motor.IsDead && !(sim.Act is DeathAct);
            if (!alive || sim.Region != Dl09Scene.Region || sim.Act is Dl09KnockbackAct) return;
            _shocked++;
            if (_shocked == 1 && !sim.Checkpoints.Flags.Has(StoryFlags.ShockedOnce))
            {
                sim.Checkpoints.SetFlag(StoryFlags.ShockedOnce, true);
                Dl09KnockbackAct.Begin(sim, -1);                                                            // knockBack(-1), L7197
            }
            else sim.Die(DeathKind.Shock);
        }
    }

    /// <summary>
    /// The cage act (<c>game.act = { kind: 'cage' }</c>, <c>updateCageAct</c> L5079–L5095), from the step after the cage takes
    /// him: he stands on the cage floor as it was at the step's start (<c>game.y = c.y</c> at #4, before <c>updateCage</c>: one
    /// step behind the cage, as the prototype has him; no ride sync, #9 places only carriers), grounded and still, easing to
    /// <c>CG.braceX</c> at <c>min(1, dt · 3)</c>, facing +1; Use pulls the pawl (<see cref="SlippingCage.PullPawl"/>, judged on
    /// the cage's y at the step's start, L5085–L5093); 0.4 s after the cage is caught the act ends there and he plays Proud
    /// (L5094). Hauled back up, or into the buffers, the cage ends it itself (the rules, at #7). It owns his pose: the motor's
    /// ride sync (<see cref="MotorSync"/>, #9) would put him on this step's floor, a step ahead of the prototype (#32).
    /// Kind <c>cage</c>, phase <c>act</c>.
    /// </summary>
    public sealed class Dl09CageAct : SceneAct
    {
        public static readonly ActId CageKind = ActId.Of("cage");

        private readonly SlippingCage _cage;
        private readonly double _yawRate;

        public Dl09CageAct(SlippingCage cage, double x, double y, double z, double yaw, MotorConfig c) : base(CageKind, ActIds.Act)
        {
            _cage = cage ?? throw new ArgumentNullException(nameof(cage));
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = c.YawRate;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                        // a.t (updateActCh1)
            Y = _cage.Y;                                                                                    // game.y = c.y, L5081
            X += (Dl09Scene.BraceX - X) * Math.Min(1, dt * Dl09Scene.BraceRate);                            // L5082
            if (input.UsePressed) _cage.PullPawl();                                                         // L5085
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);                                      // facing 1: updateCharacter
            if (_cage.RideDone)                                                                             // L5094
            {
                sim.Motor.Place(X, Y, 1, Yaw);
                Next = new QuirkAct(ClipNames.Proud, QuirkAct.ClipSeconds(ClipNames.Proud), cancel: true, startClock: sim.Clock);   // playQuirk('Proud')
                return false;
            }
            return true;
        }
    }

    /// <summary>
    /// The long hopscotch (<c>startHopscotch</c> L3437–L3441, <c>updateAct4</c> L3346–L3361; <c>HOPSCOTCH_LONG</c>, L3404–L3410):
    /// on the clip's frame (24 fps, from the step after it starts) he settles onto the mark at <c>min(1, dt · 4)</c> until f80,
    /// then the game moves his root hop by hop (each <c>dx · smooth(k)</c> along, <c>peak · sin(πk)</c> up while in the air), and
    /// stands on the deck again at f287. Moving left or jumping before f76 cancels it. It owns his pose (the motor has no
    /// root-moving clip, #28). Kind <c>hopscotch</c>, phase <c>act</c>.
    /// </summary>
    public sealed class Dl09HopscotchAct : SceneAct
    {
        public static readonly ActId HopscotchKind = ActId.Of("hopscotch");

        /// <summary><c>HOPSCOTCH_LONG</c>: startX, end, cancelUntil; the settle rate (L3349).</summary>
        public const double StartX = Dl09Lane.Off4 + 66.3, EndFrame = 287, CancelUntil = 76, SettleRate = 4;
        /// <summary>[start frame, land frame, dx, peak] per hop (L3407–L3408).</summary>
        public static readonly double[] Hops =
        {
            80, 88, 0.2333, 0.07, 91, 99, 0.2, 0.07, 102, 110, 0.2, 0.07, 113, 122, 0.2, 0.08, 126, 135, 0.2, 0.075,
            166, 175, 0.2, 0.08, 179, 190, 0.225, 0.11, 196, 207, 0, 0.08, 218, 225, 0, 0.05, 240, 249, -0.225, 0.07, 252, 261, -0.2, 0.07,
        };

        private readonly double _yawRate, _fps;

        public Dl09HopscotchAct(double x, double y, double z, double yaw, MotorConfig c) : base(HopscotchKind, ActIds.Act)
        {
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = c.YawRate; _fps = c.Fps;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                        // HopscotchLong's time (the mixer ran first)
            double f = T * _fps;
            bool left = input.Move < 0 && !input.MoveIsAnalog;
            if (f < CancelUntil && (left || input.JumpPressed)) return End(sim, dt);                        // L3348
            if (f < Hops[0]) X += (StartX - X) * Math.Min(1, dt * SettleRate);                              // L3349
            else
            {
                double x = StartX, dy = 0;
                for (int i = 0; i < Hops.Length; i += 4)
                {
                    double k = Smooth.Clamp((f - Hops[i]) / (Hops[i + 1] - Hops[i]), 0, 1);
                    x += Hops[i + 2] * Smooth.Step(k);
                    if (k > 0 && k < 1) dy += Hops[i + 3] * Math.Sin(Math.PI * k);
                }
                X = x; Y = Dl09Lane.Deck + dy;                                                              // L3358
            }
            if (f >= EndFrame) return End(sim, dt);                                                         // L3361
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);
            return true;
        }

        private bool End(ChapterSim sim, double dt)
        {
            Y = Dl09Lane.Deck;                                                                              // game.y = DECK; facing 1
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);
            sim.Motor.Place(X, Y, 1, Yaw);
            return false;
        }
    }

    /// <summary>
    /// The city (<c>game.act = { kind: 'awe' }</c>, L3433; <c>updateAct4</c> L3378–L3398): he turns out to the atrium (yaw π, at
    /// <c>updateCharacter</c>'s 8 rad/s), plays <c>Awe</c> to f158, held on the <c>refuge</c> moment's clock until it lets him go
    /// (16.6 s, or a touch of the controls from 14 s: <c>momentFree</c>, L953–L957), and turns home (π/2). It owns his pose
    /// (the motor cannot hold a yaw of its own, #28). Kind <c>awe</c>, phases <c>turn</c>, <c>act</c>, <c>back</c>.
    /// </summary>
    public sealed class Dl09AweAct : SceneAct
    {
        public static readonly ActId AweKind = ActId.Of("awe"), Turn = ActId.Of("turn"), Back = ActId.Of("back");
        /// <summary>The turn is done within 0.05 rad (L3381, L3394); <c>Awe</c> ends at f158 (L3378).</summary>
        public const double Within = 0.05, EndFrame = 158;

        private readonly MomentDirector _moment;
        private readonly double _yawRate, _fps;
        private double _clipT;

        public Dl09AweAct(MomentDirector moment, double x, double y, double z, double yaw, MotorConfig c) : base(AweKind, Turn)
        {
            _moment = moment ?? throw new ArgumentNullException(nameof(moment));
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = c.YawRate; _fps = c.Fps;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                        // a.t (updateAct)
            if (Phase == Turn)
            {
                if (Math.Abs(Yaw - Math.PI) < Within) { Phase = ActIds.Act; _clipT = 0; }  // L3381
                Yaw = Smooth.MoveTowards(Yaw, Math.PI, _yawRate * dt);                                      // yawOverride π
                return true;
            }
            if (Phase == ActIds.Act)
            {
                _clipT += dt;                                                                               // Awe's time: the mixer ran first
                double? t = _moment.Time(sim.Clock);
                bool done = _clipT * _fps >= EndFrame;                                                      // L3389
                if (done && t != null && t.Value < PrologueMoments.Refuge.ActLetsGoAt) done = _moment.Free(PrologueMoments.Refuge, t, MomentDirector.AnyInput(input));
                if (done) Phase = Back;
                Yaw = Smooth.MoveTowards(Yaw, done ? Math.PI / 2 : Math.PI, _yawRate * dt);
                return true;
            }
            if (Math.Abs(Yaw - Math.PI / 2) < Within)                                                        // L3394
            {
                Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);
                sim.Motor.Place(X, Y, 1, Yaw);
                return false;
            }
            Yaw = Smooth.MoveTowards(Yaw, Math.PI / 2, _yawRate * dt);
            return true;
        }
    }

    /// <summary>
    /// The first touch of a live arc (<c>knockBack(−1)</c>, L7197–L7202; the act, <c>updateActCh1</c> L4410–L4413): he lets go of
    /// what he holds and is thrown back along the lane at <c>dir · 0.9 · max(0, 0.4 − t) · 2.5</c> m/s while <c>Knockback</c>
    /// plays (40 frames), then stands. It owns his pose (the motor has no knock-back, #32). Kind <c>knockback</c>, no phase.
    /// </summary>
    public sealed class Dl09KnockbackAct : SceneAct
    {
        public static readonly ActId KnockbackKind = ActId.Of("knockback");
        public const string Clip = "Knockback";
        public const double Speed = 0.9, Over = 0.4, Gain = 2.5;

        private readonly int _dir, _facing;
        private readonly double _seconds, _yawRate;

        private Dl09KnockbackAct(int dir, int facing, double x, double y, double z, double yaw, double yawRate) : base(KnockbackKind, ActId.None)
        {
            _dir = dir; _facing = facing; X = x; Y = y; Z = z; Yaw = yaw; _yawRate = yawRate;
            _seconds = QuirkAct.ClipSeconds(Clip);
        }

        /// <summary><c>knockBack(dir)</c>: not during another act (L7198); <c>releaseHolds</c>, then the act, <c>game.vx = 0</c>.</summary>
        public static bool Begin(ChapterSim sim, int dir)
        {
            if (sim.Busy) return false;
            var m = sim.Motor;
            double x = sim.X, y = sim.Y;
            if (m.Hold == HoldKind.Item && m.Carried is CarriedItem item) item.Drop(x, Math.Max(0, y));    // releaseHolds, L7425–L7428
            m.Place(x, y, m.Facing, m.Yaw);
            sim.StartAct(new Dl09KnockbackAct(dir, m.Facing, x, y, sim.Z, sim.Yaw, sim.Config.YawRate));
            return true;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                                        // a.t
            X += _dir * Speed * Math.Max(0, Over - T) * dt * Gain;                                          // L4411
            Yaw = Smooth.MoveTowards(Yaw, _facing * Math.PI / 2, _yawRate * dt);
            if (T >= _seconds)                                                                              // L4412
            {
                sim.Motor.Place(X, Y, _facing, Yaw);
                return false;
            }
            return true;
        }
    }
}
