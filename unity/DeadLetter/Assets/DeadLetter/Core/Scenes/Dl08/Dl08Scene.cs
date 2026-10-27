using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes.Dl06;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;

namespace DeadLetter.Core.Scenes.Dl08
{
    /// <summary>
    /// DL-08 The Handbrake (port_architecture §5; docs/scenes/DL-08_the_handbrake.md §1–9 and its passes): through the
    /// residential doorway into the goods hall of Lift 2 (<c>goods</c>, region 4). Load on the pan raises the platform from
    /// the bottom of its flooded shaft: D-17 alone halfway, the goods trolley with its ballast to the landing. Stepped on
    /// unlatched it drops under him and he scrambles back (Teeter); the pawl lever at the shaft's edge drops the dog home
    /// only with the platform at the landing (LeverPull, else LeverStuck), and then the trolley rolls on across it to the far
    /// landing's rail. Past the shaft with the pawl set: <c>latched</c>, and the returns belt starts (bells, klaxon) and runs
    /// against him with crates to hop or climb, to the end of the belt at <c>CG.x0</c> (97.6), where DL-09 begins. Region 4;
    /// lines are index.html at 7b3c123 (<c>DL04</c> in its names: L3002–L3445, L7328–L7329, L7371–L7376).
    /// <para>Not ported here: the White in the shaft's sump (its first sight as the platform first rises, <c>sumpShown</c>
    /// L7372; the scare and its slap, the knockback: the beings system's, §4.15) beyond its one effect on him, that he goes
    /// carefully by the water with auto-run on (<c>wantsRun</c>, L1925, <see cref="Handbrake08.CarefulX0"/>); the idle look
    /// down the shaft (<c>PEEK_SPOTS.shaft</c>, L3862: the idle clock, <c>input.lastActivity</c>, is not in Core); the Pat
    /// (never played: <c>resetCh1</c> sets <c>dl4.patted</c>, L4124); the camera's platform look; the lamps, the drum and the
    /// chains (the view's, from the mechanisms).</para>
    /// </summary>
    public static class Dl08Scene
    {
        public const string Id = "DL-08";

        /// <summary>Region 4 begins at the doorway (<c>REGION4_X</c>, L2044); DL-08 ends at <c>CG.x0</c> (L3899, L8143).</summary>
        public const double X0 = Dl08Lane.Region4X, X1 = Dl08Lane.X1;

        /// <summary>The checkpoints (<see cref="ChapterDefs.PrologueCheckpoints"/>): <c>goods</c> (DL-07's rules reach it at the doorway, L2044), <c>latched</c> (L3419).</summary>
        public const string GoodsCheckpoint = "goods", LatchedCheckpoint = "latched";
        /// <summary><c>latched</c>: grounded past <c>SHAFT.x1 + 0.35</c> and short of <c>BELT4.x0</c>, the pawl set, from <c>goods</c> (L3419).</summary>
        public const double LatchedX0 = Dl08Lane.ShaftX1 + 0.35, LatchedX1 = Dl08Lane.BeltX0;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Handbrake",
            X0 = X0, X1 = X1,
            Region = Dl08Lane.Region,
            Mechanisms = Mechanisms(),
            // grab4R (L3271–L3273): the trolley from its right too.
            Interactables = g => new IInteractable[] { new PushTwin(g.Get<Pushable>("dl08.trolley")) },
            Lane = Dl08Lane.Table,
            LaneContributors = Dl08Lane.Contributors,
            Rules = () => new Handbrake08(),
        };

        /// <summary>
        /// The prototype's order: <c>updatePlayer</c> moves the trolley (#4, <c>updateHold</c>, L2337–L2348) and the pawl's
        /// lever act drops the dog (L3316–L3318); then <c>updateDL04</c> (#6): the pan's load, the platform (L3176–L3197;
        /// the pawl first, so it holds it this step), the belt and its crates (L3218–L3225, <c>updateCrates</c>).
        /// </summary>
        public static MechanismDef[] Mechanisms() => new[]
        {
            new MechanismDef("dl08.trolley", () => new Pushable("dl08.trolley", PushableParams.Dl08Trolley())),
            new MechanismDef("dl08.pan", () => new LoadPlate("dl08.pan", LoadPlateParams.Dl08Pan())),
            new MechanismDef("dl08.pawl", () => new Pawl("dl08.pawl", PawlParams.Dl08Pawl())),
            new MechanismDef("dl08.platform", () => new CounterweightLift("dl08.platform", CounterweightLiftParams.Dl08Platform())),
            new MechanismDef("dl08.belt", () => new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt())),
        };
    }

    /// <summary>
    /// DL-08's rules (<c>updateTriggers4</c> L3412–L3437, <c>updateAct4</c> L3290–L3337, <c>updateDL04</c> L3171–L3259, the
    /// sump in <c>updateCh1</c> L7371–L7376): the Teeter act when the platform drops under him (<see cref="Dl08TeeterAct"/>);
    /// Proud once he has stepped back from setting the pawl (L3299); the Startle at a crash nearby (L3195); <c>latched</c>
    /// past the shaft (L3419); careful by the sump's water (L1925); falling into the shaft (L7373–L7375); climbing a crate as
    /// the belt carries it (<see cref="Dl08BeltMantleAct"/>); the way back into region 3 (L2045). Cues: the shakes, the
    /// <c>latch</c> sting.
    /// <para><b>Always.</b> The prototype runs <c>updateTriggers4</c> wherever he is in region 4, and the belt runs to DL-09's
    /// door; so these run every step, guarded by region 4 (and by x where the prototype guards).</para>
    /// </summary>
    public sealed class Handbrake08 : SceneRules
    {
        public static readonly CueId Shake = ReturnToSender06.Shake, MusicLatch = CueId.Of("music:latch");
        /// <summary>Shakes, in hundredths: the teeter 0.3 (L3281), the pawl's click 0.22 (L3125).</summary>
        public const int TeeterShake = 30, PawlShake = 22;
        /// <summary>
        /// Careful by the sump's water (<c>wantsRun</c>, L1925): the White's water (<c>sump7</c>, 85.8–88.3, part
        /// <c>scare</c>, L7328) is his in region 4 while x &lt; 91.3, and within 2 m of it auto-run walks.
        /// </summary>
        public const double CarefulX0 = Dl08Lane.ShaftX0 - 2.0, CarefulX1 = Dl08Lane.ShaftX1 + 2.0;
        /// <summary>The sump: below −0.2 between 85.9 and 88.2 he is dragged under (<c>die('grabbed', { hold: 1.3 })</c>, sinking 0.8 m/s, L7373–L7375).</summary>
        public const double SumpX0 = Dl08Lane.ShaftX0 + 0.1, SumpX1 = Dl08Lane.ShaftX1 - 0.1, SumpY = -0.2, SumpSink = 0.8, SumpHold = 1.3;

        private Pushable _trolley;
        private Pawl _pawl;
        private CounterweightLift _platform;
        private ReturnsBelt _belt;
        private bool _latched;

        public override bool Always => true;

        public Pushable Trolley => _trolley;
        public LoadPlate Pan { get; private set; }
        public Pawl Pawl => _pawl;
        public CounterweightLift Platform => _platform;
        public ReturnsBelt Belt => _belt;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _trolley = g.Get<Pushable>("dl08.trolley");
            Pan = g.Get<LoadPlate>("dl08.pan");
            _pawl = g.Get<Pawl>("dl08.pawl");
            _platform = g.Get<CounterweightLift>("dl08.platform");
            _belt = g.Get<ReturnsBelt>("dl08.belt");
            _trolley.CanStandAt = x => StandFree(sim, x);
            _latched = false;
        }

        /// <summary>
        /// <c>nearUse4</c>'s stand point (L3271–L3272): nothing under its feet above the deck (support &lt; DECK + 0.05), past
        /// the door and 0.2 short of the shaft.
        /// </summary>
        public static bool StandFree(ChapterSim sim, double x)
            => sim.Lane.SupportAt(x) < Dl08Lane.Deck + 0.05 && x > Dl08Lane.Door4X && x < Dl08Lane.ShaftX0 - 0.2;

        /// <summary>#4's head: careful by the water (<c>wantsRun</c> reads last step's water and his x then, L1925).</summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            if (sim.Region != Dl08Lane.Region) return;
            double x = sim.Motor.X;
            sim.Motor.Careful = x > CarefulX0 && x < CarefulX1;
        }

        /// <summary>
        /// #4's tail: a climb onto a crate on the running belt (the prototype carries the climb along, L1942); Proud once he
        /// has stepped back from setting the pawl (L3299); <c>latched</c> past the shaft (L3419, reached at the step's end);
        /// back into region 3 left of the doorway (L2045, free movement only).
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            if (sim.Region != Dl08Lane.Region) return;
            var m = sim.Motor;
            if (m.IsMantling && MantleStarted(m) && m.X > Dl08Lane.BeltX0 && m.X < Dl08Lane.BeltX1) sim.StartAct(new Dl08BeltMantleAct(_belt, m));   // L1942
            if (sim.MotorActEndedOn == _pawl && _pawl.Engaged) SceneQuirk.Start(sim, ClipNames.Proud, cancel: true);   // playQuirk('Proud'), L3299
            if (!freeStep) return;
            double x = m.X;
            if (m.Grounded && _pawl.Engaged && x > Dl08Scene.LatchedX0 && x < Dl08Scene.LatchedX1
                && sim.Checkpoints.Current.Name == Dl08Scene.GoodsCheckpoint) _latched = true;                         // L3419
            if (x < Dl08Lane.Region4X - 0.2) sim.SetRegion(Dl08Lane.Region - 1);                                       // L2045
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            for (int i = 0; i < log.Count; i++)
            {
                var e = log[i];
                if (e.Kind != MechanismEventKind.Event || !(e.Id == _platform.Id)) continue;
                switch ((CounterweightLiftEvent)e.Code)
                {
                    case CounterweightLiftEvent.Teeter:                                                        // startTeeter, L3277–L3282
                        sim.StartAct(new Dl08TeeterAct(_platform, sim.X, sim.Y, sim.Z, sim.Yaw, sim.Motor.Facing, e.Value, sim.Config.YawRate));
                        sim.Cue(Shake, TeeterShake);
                        break;
                    case CounterweightLiftEvent.Crash:                                                         // shake(0.55 · v), L3193
                        sim.Cue(Shake, (int)Math.Round(55 * Math.Min(1, e.Value / 3)));
                        break;
                    case CounterweightLiftEvent.Startle:                                                       // L3195
                        SceneQuirk.Start(sim, ClipNames.Startle, cancel: true);
                        break;
                }
            }
            if (log.Has(_pawl.Id, MechanismEventKind.State, (int)PawlState.Engaged)) { sim.Cue(Shake, PawlShake); sim.Cue(MusicLatch); }   // latchPawl, L3122–L3126
            if (_latched) { _latched = false; sim.Checkpoints.Reach(Dl08Scene.LatchedCheckpoint); }
            // updateCh1's hazards (L7373–L7375): down in the shaft's water he is dragged under.
            if (sim.Region == Dl08Lane.Region && sim.X > SumpX0 && sim.X < SumpX1 && sim.Y < SumpY)
                sim.Die(DeathKind.Grabbed, SumpSink, SumpHold);
        }

        private static bool MantleStarted(D17Motor m)
        {
            var ev = m.Events;
            for (int i = 0; i < ev.Count; i++) if (ev[i].Kind == MotorEventKind.MantleStart) return true;
            return false;
        }
    }

    /// <summary>
    /// Onto the unlatched platform: it drops under him and he scrambles back (<c>game.act = { kind: 'teeter' }</c>, L3277–L3282,
    /// L3329–L3337). The clip Teeter from its start: until f12 he rides the platform down (<c>game.y = platTop()</c>), then over
    /// ten frames he is lifted back to 0.28 outside the nearer edge (smoothstep in x, an arc 0.3 high, from the platform's top
    /// to the deck); at f22 he lands and the platform stops dipping (<c>plat.lurch = false</c>); at f37 he stands on the deck.
    /// The motor has no such act (the platform moves him); it owns his pose. Named for the platform (its phase Teeter).
    /// </summary>
    public sealed class Dl08TeeterAct : SceneAct
    {
        public static readonly ActId PlatformKind = ActId.Of("dl08.platform"), TeeterPhase = ActId.Of("Teeter");
        /// <summary>The clip's frames (L3331–L3336).</summary>
        public const double LiftFrame = 12, LiftFrames = 10, LandFrame = 22, EndFrame = 37, Arc = 0.3;

        private readonly CounterweightLift _platform;
        private readonly double _fromX, _back, _yawRate;
        private readonly int _facing;
        private bool _landed;

        /// <param name="back">Where he scrambles back to (the platform's Teeter event's value).</param>
        public Dl08TeeterAct(CounterweightLift platform, double x, double y, double z, double yaw, int facing, double back, double yawRate)
            : base(PlatformKind, TeeterPhase)
        {
            _platform = platform ?? throw new ArgumentNullException(nameof(platform));
            X = x; Y = y; Z = z; Yaw = yaw;
            _fromX = x; _back = back; _facing = facing >= 0 ? 1 : -1; _yawRate = yawRate;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                   // the mixer advanced the clip before updatePlayer
            double f = T * 24, top = _platform.FloorY;                                // actions.Teeter.time · FPS; platTop() (last step's)
            if (f < LiftFrame) Y = top;
            else
            {
                double k = Math.Min(1, (f - LiftFrame) / LiftFrames);
                X = _fromX + (_back - _fromX) * Smooth.Step(k);
                Y = top * (1 - k) + Dl08Lane.Deck * k + Arc * Math.Sin(Math.PI * k);
            }
            if (f >= LandFrame && !_landed) { _landed = true; _platform.EndLurch(); Y = Dl08Lane.Deck; }
            Yaw = Smooth.MoveTowards(Yaw, _facing * Math.PI / 2, _yawRate * dt);       // updateCharacter: his facing
            if (f >= EndFrame)
            {
                Y = Dl08Lane.Deck;
                sim.Motor.Place(X, Y, _facing, Yaw);                                   // act = null, grounded, Idle (L3336)
                return false;
            }
            return true;
        }
    }

    /// <summary>
    /// A climb started over the belt (onto a crate): the prototype carries the climb along with it (<c>m.x0 −= BELT4.speed · dt</c>
    /// each step while the belt runs and he is over it, L1942). The motor's mantle cannot be moved (#32), so this act stands in
    /// from the climb's start: it steps the motor (its mantle keys run as they would) and reports its pose shifted by the
    /// belt's carry so far; at the climb's end it hands the motor that x. Named as the motor's climb (<c>mantle</c>).
    /// </summary>
    public sealed class Dl08BeltMantleAct : SceneAct
    {
        public static readonly ActId MantleKind = ActId.Of("mantle");

        private readonly ReturnsBelt _belt;
        private double _shift;
        private bool _grounded;

        /// <param name="m">The motor, on the step its climb started.</param>
        public Dl08BeltMantleAct(ReturnsBelt belt, D17Motor m) : base(MantleKind, ActId.None)
        {
            _belt = belt ?? throw new ArgumentNullException(nameof(belt));
            X = m.X; Y = m.Y; Z = m.Z; Yaw = m.Yaw; _grounded = m.Grounded;
        }

        public override bool OwnsPose => true;
        /// <summary>As the motor's climb keeps it (a climb caught in the air stays ungrounded).</summary>
        public override bool PoseGrounded => _grounded;
        /// <summary>How far the belt has carried the climb, metres (+x).</summary>
        public double Shift => _shift;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            _shift += _belt.CarryVelocity(X) * dt;                                    // L1942: before the climb's step, at his x now
            var m = sim.Motor;
            m.Step(input, dt);
            X = m.X + _shift; Y = m.Y; Z = m.Z; Yaw = m.Yaw; _grounded = m.Grounded;
            if (m.IsMantling) return true;
            var s = m.Capture();                                                       // the climb is over: he stands where it left him
            s.X = X;
            m.SetState(s);
            return false;
        }
    }
}
