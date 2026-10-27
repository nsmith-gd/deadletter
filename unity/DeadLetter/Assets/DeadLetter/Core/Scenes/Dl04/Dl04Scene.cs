using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;

namespace DeadLetter.Core.Scenes.Dl04
{
    /// <summary>
    /// DL-04 The Racks (port_architecture §5; docs/scenes/DL-04_the_racks.md): past DL-03's gate the racks are revealed;
    /// among the dormant couriers he stops and understands (the <c>kin</c> moment) and walks on slowly; at the end of the
    /// hall the bay reads only him, until he drags the fallen courier onto its plate: the cradle seats it, the door opens
    /// and stays open, he touches its head once and goes on. Region 2 from the gate (30.6) to the Ration Hall (47.9,
    /// <c>sceneName</c> L8139). Lines are index.html at 7b3c123 (module names lag: <c>buildDL02/updateDL02</c> = DL-03 and
    /// DL-04's reveal; <c>updateCh1</c> = the bay).
    /// <para>Not here: the curiosity at the empty rack (<c>SitRack</c>, L5112; §4.27, as DL-02's), and the optional nudge
    /// of a near-row courier (<c>dl04.nudge</c>, L2250, L2291–L2309), whose spot is the art's (<c>refs.nudgeAt</c>, from the
    /// set's marker, L2185), not a constant of the game's.</para>
    /// </summary>
    public static class Dl04Scene
    {
        public const string Id = "DL-04";

        /// <summary><c>GATE_X</c> (L323): DL-04 begins at x ≥ GATE_X; <c>RATION5.x0</c> = OFF2 + 34.9 (L3447): DL-05 begins (L8139).</summary>
        public const double X0 = Dl03Lane.GateX, X1 = 13 + 34.9;
        /// <summary>The racks are revealed once he is GATE_X + 0.2 in (L2401); he realises once GATE_X + 0.6 in, 1 s after (L1956).</summary>
        public const double RevealX = Dl03Lane.GateX + 0.2, RealiseX = Dl03Lane.GateX + 0.6, RealiseAfter = 1.0;
        /// <summary><c>KIN_UNTIL_X</c> = OFF2 + 23.6 and <c>SLOW_WALK</c> (L327): after the realisation he walks slowly to here (<c>paceSlow</c>, L2079).</summary>
        public const double KinUntilX = 13 + 23.6, SlowWalk = 0.39;
        /// <summary>The <c>bayTouch</c> act: he stands at <c>RK.bayX</c> + 0.42 facing −1 (L4806) and lets go at TouchHead f51 (L4493).</summary>
        public const double TouchStandX = Dl04Lane.BayX + 0.42, TouchEndFrame = 51;
        public const int TouchFace = -1;
        /// <summary>The <c>bay</c> checkpoint once past <c>RK.door.x1</c> + 0.2 (L4947); it places him at x1 + 0.4 (L7983; <see cref="PrologueCheckpoints"/>).</summary>
        public const double BayReachX = Dl04Lane.DoorX1 + 0.2, BayX = Dl04Lane.DoorX1 + 0.4;

        /// <summary>
        /// The scene definition. <paramref name="revealPending"/>: what DL-03 hands on when he walks through
        /// (<see cref="Dl03.Dl03Rules.RevealPending"/>: solved, the racks still dark until he passes the gate), which the
        /// <c>solved</c> checkpoint alone does not say (a reload there has them lit, L8029).
        /// </summary>
        public static SceneDef Def(bool revealPending = false) => new SceneDef
        {
            Id = Id,
            Title = "The Racks",
            X0 = X0, X1 = X1,
            Region = Dl04Lane.Region,
            Checkpoints = PrologueCheckpoints.Of(Id),                                           // bay (L7983); he walks in under DL-03's solved
            // Step order = the prototype's: updatePlayer drags the courier (#4, updateHoldCh1 L4683–L4735), then updateCh1's
            // bay (#7, L4783–L4816): the plate reads him, the cradle, then the door.
            Mechanisms = new[]
            {
                new MechanismDef("dl04.courier", () => new Pushable("dl04.courier", PushableParams.Dl04Courier())),
                new MechanismDef("dl04.bayPlate", () => new LoadPlate("dl04.bayPlate", LoadPlateParams.Dl04BayPlate())),
                new MechanismDef("dl04.cradle", () => new Cradle("dl04.cradle", CradleParams.Dl04Cradle())),
                new MechanismDef("dl04.bayDoor", () => new PlateDoor("dl04.bayDoor", PlateDoorParams.Dl04BayDoor())),
            },
            Interactables = g => new IInteractable[] { new PushTwin(g.Get<Pushable>("dl04.courier")) },   // courierAlt, L4291–L4294
            Lane = Dl04Lane.Table,
            LaneContributors = Dl04Lane.Contributors,
            Rules = () => new Dl04Rules(revealPending),
        };
    }

    /// <summary>
    /// DL-04's bespoke rules: the reveal once he is through the gate (<c>updateDL02</c> L2401–L2403); the realisation
    /// among the couriers, the <c>kin</c> moment (<c>updatePlayer</c> L1956–L1958, the act L2310–L2314) and the slow walk
    /// after it (<c>paceSlow</c> L2079); the courier not grabbable once the cradle has it (<c>pushHere</c>: state 'free',
    /// L4300); the touch once the cradle seats it (L4806); the <c>bay</c> checkpoint (L4947); and the way on into DL-05
    /// (<c>sceneName</c>, L8139).
    /// </summary>
    public sealed class Dl04Rules : SceneRules
    {
        /// <summary>
        /// The once-only beats (<c>once('realise')</c> L1958, <c>once('bayTouch')</c> L4806): the prototype's <c>seen</c> set,
        /// which outlives respawns (cleared only by a new game, L8058), so they are the save's seen moments: a respawn, a
        /// continue or a fresh scene at <c>bay</c> never plays them again.
        /// </summary>
        public const string SeenRealise = "realise", SeenBayTouch = "bayTouch";

        private readonly bool _handedPending;
        private bool _begun, _revealed, _revealPending, _realised, _kinSlow;              // per life: resetWorld, L8027–L8034
        private double _revealTime;
        private Pushable _courier;
        private Cradle _cradle;

        public Dl04Rules(bool revealPending = false) { _handedPending = revealPending; }

        /// <summary>The directed moment's clock and state (<c>startMoment('kin')</c>; the runtime schedules its cue).</summary>
        public MomentDirector Moment { get; } = new MomentDirector(null);
        /// <summary><c>game.revealed</c>, <c>game.revealPending</c>, <c>game.revealTime</c> (L2398–L2403, L8029).</summary>
        public bool Revealed => _revealed;
        public bool RevealPending => _revealPending;
        public double RevealTime => _revealTime;
        /// <summary><c>game.realised</c>, <c>game.kinSlow</c> (L1957–L1958, L8034).</summary>
        public bool Realised => _realised;
        public bool KinSlow => _kinSlow;

        public override void OnBegin(SceneSim sim, string checkpoint, bool fromOpening)
        {
            _courier = sim.Graph.Get<Pushable>("dl04.courier");
            _cradle = sim.Graph.Get<Cradle>("dl04.cradle");
            var cradle = _cradle;
            _courier.CanStandAt = _ => !cradle.Taken;                       // pushHere: only while 'free' (L4300)
            var cp = sim.Checkpoints.Current;
            _revealed = cp.Past("solved");                                   // resetWorld, L8029
            _revealTime = -100;
            _revealPending = false;
            if (!_begun && _handedPending && _revealed) { _revealPending = true; _revealTime = 1e9; }   // as DL-03 left it, L2398
            _realised = cp.Past("scanned");                                  // L8034
            _kinSlow = false;
            _begun = true;
            sim.Motor.SlowWalkLimit = 0;
        }

        /// <summary>
        /// #4's head (<c>updatePlayer</c>, after the act and before Use, L1955–L1959): the realisation, once he is in among the
        /// couriers a second after the reveal, standing and empty-handed. It stops him (vx = 0) and holds him in the
        /// <see cref="RealiseAct"/> on the moment's clock; and <c>paceSlow</c> (L1978, L2079) sets his pace for this step.
        /// </summary>
        public override void BeforeMotor(SceneSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (m.IsActing || m.IsMantling) return;
            if (sim.Region == Dl04Lane.Region && _revealed && !_revealPending && sim.Clock - _revealTime > Dl04Scene.RealiseAfter
                && !_realised && sim.X > Dl04Scene.RealiseX && m.Grounded && m.Hold == HoldKind.None)
            {
                _realised = true;
                if (!sim.Checkpoints.HasSeen(SeenRealise))                  // once('realise')
                {
                    sim.Checkpoints.MarkSeen(SeenRealise);
                    _kinSlow = true;
                    m.Place(m.X, m.Y, m.Facing);                            // game.vx = 0 (#28: Place is the only way)
                    Moment.Start(PrologueMoments.Kin, sim.Clock, musicAvailable: false);
                    sim.Cue("moment:kin");
                    sim.StartAct(new RealiseAct(Moment, sim.Config.Fps));
                    return;
                }
            }
            bool slow = sim.Region == Dl04Lane.Region && _realised && _kinSlow && sim.X > Dl04Scene.X0 && sim.X < Dl04Scene.KinUntilX;
            m.SlowWalkLimit = slow ? Dl04Scene.SlowWalk : 0;
        }

        public override void AfterGraph(SceneSim sim)
        {
            // updateDL02 (#6): the reveal plays the moment he is through the gate, however it was opened (L2401–L2403).
            if ((_revealPending || !_revealed) && sim.Region == Dl04Lane.Region && sim.X > Dl04Scene.RevealX)
            {
                _revealed = true; _revealPending = false; _revealTime = sim.Clock;
                sim.Checkpoints.Reach("solved");
                sim.Cue("music:racks");
            }
            // updateCh1 (#7): the cradle has seated the courier: he goes to it, once (L4806).
            if (sim.Graph.Log.Has("dl04.cradle", MechanismEventKind.Event, (int)CradleEvent.Seat) && !sim.Checkpoints.HasSeen(SeenBayTouch))
            {
                sim.Checkpoints.MarkSeen(SeenBayTouch);
                sim.StartAct(new BayTouchAct(sim.X, sim.Y, sim.Z, sim.Yaw, Dl04Scene.TouchStandX, Dl04Scene.TouchFace, sim.Config));
            }
            // The bay checkpoint, through the door (L4947).
            if (sim.Region == Dl04Lane.Region && sim.X > Dl04Scene.BayReachX) sim.Checkpoints.Reach("bay");
            // sceneName (L8139): from RATION5.x0 it is DL-05.
            if (!sim.Exited && sim.X >= Dl04Scene.X1) sim.Exit();
        }
    }

    /// <summary>
    /// The realisation (<c>realise</c>, L1958, L2310–L2314): he stands with the <c>Realise</c> clip, held on the <c>kin</c>
    /// cue's clock. Once the clip is past f155 and the cue past 9.5 s he idles; from then the moment frees him at
    /// <c>control</c> (22.5 s), or at any touch of the controls after <c>lock</c> (19 s) (<c>momentFree</c>, L953–L957). The
    /// prototype starts it in place of his step and returns, so its first update is the next step's. The motor stands
    /// meanwhile (no input).
    /// </summary>
    public sealed class RealiseAct : SceneAct
    {
        private readonly MomentDirector _moment;
        private readonly double _fps;
        private bool _fresh = true;

        public RealiseAct(MomentDirector moment, double fps) : base("realise", "act")
        {
            _moment = moment ?? throw new ArgumentNullException(nameof(moment));
            _fps = fps;
        }

        /// <summary><c>a.idle</c>: the hand off his chest, standing while the camera pulls away (L2313).</summary>
        public bool Idle { get; private set; }

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            if (_fresh) { _fresh = false; return true; }                    // started this step (L1958 returns)
            T += dt;                                                        // the Realise clip's time (the mixer ran after the step it started)
            double? t = _moment.Time(sim.Clock);
            if (!Idle && T * _fps >= PrologueMoments.KinIdleFrame && (t == null || t > PrologueMoments.KinIdleAfter)) Idle = true;   // L2313
            return !(Idle && _moment.Free(PrologueMoments.Kin, t, MomentDirector.AnyInput(input)));                         // L2314
        }
    }

    /// <summary>
    /// The touch (<c>bayTouch</c>, L4806, L4491–L4495): once the cradle seats the courier he walks to it (<c>approachCh1</c>
    /// L4380–L4388: facing <c>face</c>, back onto the lane at 0.45 m/s, along it at WALK · 0.8, there within 0.012 and 0.004),
    /// lays his claw on its head (<c>TouchHead</c>) and lets go at f51, facing +1 again. It owns his pose (the motor has no
    /// such act, #22); his yaw turns as <c>updateCharacter</c> turns it (8 rad/s, L7579–L7583).
    /// <para>At the end the motor is put back at rest where he stands (<see cref="D17Motor.Place"/>) facing the courier, and
    /// stepped once with a vanishing stick (<see cref="double.Epsilon"/>): that faces him +1 and starts his yaw's turn on
    /// the prototype's step without moving him (#28, M9: the motor cannot be turned in place).</para>
    /// </summary>
    public sealed class BayTouchAct : SceneAct
    {
        private readonly double _standX;
        private readonly int _face;
        private readonly MotorConfig _c;

        public BayTouchAct(double x, double y, double z, double yaw, double standX, int face, MotorConfig c) : base("bayTouch", "approach")
        {
            X = x; Y = y; Z = z; Yaw = yaw;
            _standX = standX; _face = face; _c = c ?? throw new ArgumentNullException(nameof(c));
        }

        public override bool OwnsPose => true;

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            if (Phase == "approach")
            {
                double dx = _standX - X, dz = 0 - Z;                                                         // L4381
                if (dz != 0) Z += Smooth.Sign(dz) * Math.Min(Math.Abs(dz), _c.StepInSpeed * dt);          // L4382
                if (Math.Abs(dx) < _c.ArriveX && Math.Abs(dz) < _c.ArriveZ) { X = _standX; Phase = "act"; T = 0; }   // L4383
                else X += Smooth.Sign(dx) * Math.Min(Math.Abs(dx), _c.Walk * _c.ApproachFactor * dt);    // L4384
                Turn(dt);
                return true;
            }
            T += dt;                                                                                         // TouchHead's time
            if (T * _c.Fps >= Dl04Scene.TouchEndFrame)                                                       // L4493
            {
                var m = sim.Motor;
                m.Place(X, Y, _face);
                m.Step(new MotorInput { Move = double.Epsilon }, dt);                                       // game.facing = 1; updateCharacter
                return false;
            }
            Turn(dt);
            return true;
        }

        private void Turn(double dt) => Yaw = Smooth.MoveTowards(Yaw, _face * Math.PI / 2, _c.YawRate * dt);
    }
}
