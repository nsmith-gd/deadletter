using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl05
{
    /// <summary>
    /// DL-05 The Ration Hall (port_architecture §5; docs/scenes/DL-05_the_ration_hall.md, pass 4's weigh-in): the hatch
    /// opens only while the WEIGH-IN plate in front of it reads a person. He is too light (UNDER), the drum too heavy
    /// (OVER); pushed on, the drum runs past the plate to the wall by the hatch, and the body dragged onto the plate reads
    /// PERSON: held a second, the hatch winds up to a crawl and the SERVED flag drops. Region 2 from <c>RATION5.x0</c>
    /// (47.9) to <c>REGION3_X</c> (60.3), where region 3 and DL-06 begin (<c>sceneName</c>, L8139; L2042). Lines are
    /// index.html at 7b3c123.
    /// </summary>
    public static class Dl05Scene
    {
        public const string Id = "DL-05";

        /// <summary><c>RATION5.x0</c> (L3447): DL-04 ends, DL-05 begins (L8139).</summary>
        public const double X0 = Dl05Lane.HallX0;
        /// <summary><c>REGION3_X</c> (L2457): past it he is in region 3 (L2042), which is DL-06.</summary>
        public const double X1 = Dl05Lane.Region3X;

        /// <summary><c>RH5</c> (L3451–L3454): the drum's start, its stop on the plate and at the wall; its grip gap.</summary>
        public const double Drum0 = 13 + 40.45, DrumPlate = 13 + 41.80, DrumPark = 13 + 43.02, DrumGap = 0.55, DrumHalf = 0.225;
        /// <summary><c>RH5</c> (L3452): the body's start and its place on the plate; its half-length and grip gap.</summary>
        public const double Body0 = 13 + 39.30, BodyPlate = 13 + 41.80, BodyHalf = 0.83, BodyGap = 1.05;

        /// <summary>Reached on the lane past these (<c>updateCh1</c>, L4935, L4936, L4947): <c>RATION5.x0 + 0.6</c>, <c>RH5.crawl[1] + 0.25</c>, <c>RK.door.x1 + 0.2</c>.</summary>
        public const double RationAt = X0 + 0.6, HatchAt = Dl05Lane.CrawlX1 + 0.25, BayAt = 46.7 + 0.2;
        /// <summary>The label check by the child's drawing: <c>RATION5.x0 + 4.0 &lt; x &lt; RATION5.x0 + 6</c> (L4941).</summary>
        public const double LabelX0 = X0 + 4.0, LabelX1 = X0 + 6;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Ration Hall",
            X0 = X0, X1 = X1,
            Region = Dl05Lane.Region,                                                    // its checkpoints: ration, hatch (L7984–L7985)
            // Step order = the prototype's: updatePlayer moves the drum and the body (#4, updateHoldCh1 L4684–L4735), then
            // updateCh1 weighs the plate, winds the hatch and drops the flag (#7, L4878–L4921).
            Mechanisms = new[]
            {
                new MechanismDef("dl05.drum", () => new Pushable("dl05.drum", DrumParams())),
                new MechanismDef("dl05.body", () => new Pushable("dl05.body", BodyParams())),
                new MechanismDef("dl05.weighIn", () => new WeighScale("dl05.weighIn", WeighScaleParams.Dl05WeighIn())),
                new MechanismDef("dl05.hatch", () => new Door("dl05.hatch", PlateOutputs.Dl05Hatch())),
                new MechanismDef("dl05.servedFlag", () => new Door("dl05.servedFlag", PlateOutputs.Dl05ServedFlag())),
            },
            // Pass 10's twins (L4291–L4294): the drum from its right, the body from its left (grip 0.06 in front, L4295).
            Interactables = g => new IInteractable[]
            {
                new PushTwin(g.Get<Pushable>("dl05.drum")),
                new PushTwin(g.Get<Pushable>("dl05.body"), forwardReach: 0.06),
            },
            Lane = Dl05Lane.Table,
            LaneContributors = Dl05Lane.Contributors,
            Rules = () => new WeighIn05(),
        };

        /// <summary>
        /// The ration drum (<c>PUSHABLES.drum</c>, L4277): pushed from its left (gap 0.55) at 0.3 m/s from 53.45; its travel
        /// ends on the plate (54.8) until it is within 0.01 of it, then at the wall by the hatch (56.02), where it is set
        /// (<c>'set'</c>, L4728). Set from <c>hatch</c> on (L4104). Chapter 1's hold acceleration, 1.4 (L4690).
        /// </summary>
        public static PushableParams DrumParams() => new PushableParams
        {
            StartX = Drum0,
            ParkedAfter = "hatch", ParkedX = DrumPark, ParkedState = PushableState.Docked,
            Side = +1, Gap = DrumGap, Speed = 0.3, Accel = 1.4,
            Min = Drum0, Max = DrumPark, StopAt = DrumPlate,
            DockAt = DrumPark, DockTolerance = 0.01,                                    // |s.x − drumPark| < 0.01, L4728
            FloorY = 0, Z = 0, ForwardReach = 0.34, BackReach = 0.34,                   // floor: 0, z: 0; p.fwd ?? 0.34, L4254
            Half = DrumHalf,
        };

        /// <summary>
        /// The body (<c>PUSHABLES.body</c>, L4279–L4281): dragged by the rope at its feet, walking backwards (side −1, gap
        /// 1.05) at 0.2 m/s from 52.3 to the plate (54.8), where it lies (<c>'plate'</c>, L4729); it stops 0.02 short of the
        /// drum while the drum is ahead of it (<c>d.x − 0.225 − bodyHalf − 0.02</c>) and can be taken hold of only while it
        /// can move more than 0.05 (<c>avail</c>). On the plate from <c>hatch</c> on (L4105).
        /// </summary>
        public static PushableParams BodyParams() => new PushableParams
        {
            StartX = Body0,
            ParkedAfter = "hatch", ParkedX = BodyPlate, ParkedState = PushableState.Docked,
            Side = -1, Gap = BodyGap, Speed = 0.2, Accel = 1.4,
            Min = Body0, Max = BodyPlate,
            Blocks = new[] { new PushBlock("dl05.drum", DrumHalf + BodyHalf + 0.02) },
            MinRoom = 0.05,
            DockAt = BodyPlate, DockTolerance = 0.01,                                   // |s.x − bodyPlate| < 0.01, L4729
            FloorY = 0, Z = 0, ForwardReach = 0.34, BackReach = 0.34,
            Half = BodyHalf,
        };
    }

    /// <summary>
    /// DL-05's rules around the weigh-in (port_architecture §2 <c>WeighIn05</c>; the scale, the hatch and the flag are
    /// mechanisms): the first time he takes hold of the body he stands over it a moment (<c>grabPush</c>'s
    /// <c>'hesitate'</c>, L4463–L4466); laid on the plate, 1.6 s later he pats the sheet (L4729–L4731); the checkpoints
    /// <c>bay</c>, <c>ration</c> and <c>hatch</c> (L4935–L4936, L4947); the label check by the child's drawing
    /// (<c>label5</c>, L4940–L4944); and the switch to region 3, which is DL-06 (L2042, L8139).
    /// </summary>
    public sealed class WeighIn05 : SceneRules
    {
        /// <summary><c>a.t &gt; 1.6</c> (L4466).</summary>
        public const double HesitateSeconds = 1.6;
        /// <summary>
        /// <c>setTimeout(…, 1600)</c> (L4731). Timeouts run on game time between steps: this one after the 96th step from
        /// the one that set it (the recorder's virtual clock, tools/sim/record_trace.mjs, shows its effects on that step).
        /// </summary>
        public const double PatDelay = 1.6;

        /// <summary>
        /// The once-only beats (<c>seen.add('bodyGrab')</c> L4463, <c>seen.add('label5')</c> L4944): the prototype's
        /// <c>seen</c> set, which outlives respawns (cleared only by a new game, L8058), so they are the save's seen moments.
        /// </summary>
        public const string SeenBodyGrab = "bodyGrab", SeenLabel = "label5";

        private Pushable _drum, _body;
        private IPushable[] _faces = Array.Empty<IPushable>();
        private CheckpointService _save;
        private int _bodyGrabSeen, _labelSeen;                                         // handles in _save.Seen
        private ActPhase _lastPhase;
        private double _patAt = double.NaN;

        public Pushable Drum => _drum;
        public Pushable Body => _body;
        /// <summary>He has taken hold of the body once (<c>seen.has('bodyGrab')</c>): no more hesitation.</summary>
        public bool BodyGrabbed => _save != null && _save.Seen.Get(_bodyGrabSeen);
        /// <summary>The label check has played (<c>seen.has('label5')</c>).</summary>
        public bool LabelSeen => _save != null && _save.Seen.Get(_labelSeen);
        /// <summary>Game-clock time the pat is due (NaN: none pending).</summary>
        public double PatAt => _patAt;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _save = sim.Checkpoints;
            _bodyGrabSeen = _save.Seen.Resolve(SeenBodyGrab);
            _labelSeen = _save.Seen.Resolve(SeenLabel);
            _drum = sim.Graph.Get<Pushable>("dl05.drum");
            _body = sim.Graph.Get<Pushable>("dl05.body");
            // The faces in the prototype's PUSHABLES order (drum, body, then the twins, L4273–L4295).
            _faces = new IPushable[] { _drum, _body, TwinOf(sim, _drum), TwinOf(sim, _body) };
            _drum.CanStandAt = stand => GripWins(sim, _drum, stand);
            _body.CanStandAt = stand => GripWins(sim, _body, stand);
            _patAt = double.NaN;                     // nothing kills here, so no timeout is pending across a rebuilt world
            _lastPhase = ActPhase.None;
        }

        /// <summary>
        /// The first grab of the body (L4463–L4466): the prototype stands him there for 1.6 s between the approach and the
        /// Grab clip. The motor goes straight into the clip on arrival and has no pause (U-11 gap, #22), so the scene holds the
        /// motor still meanwhile (<see cref="Dl05HesitateAct"/>) and lets it go on into the clip from where it was.
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            var m = sim.Motor;
            var phase = m.IsActing ? m.ActPhase : ActPhase.None;
            if (m.IsActing && m.ActVerb == Verb.Grab && phase == ActPhase.Clip && _lastPhase == ActPhase.Approach && IsBody(sim.MotorActTarget)
                && !BodyGrabbed)
            {
                _save.MarkSeen(SeenBodyGrab);
                sim.StartAct(new Dl05HesitateAct(_body.Id.Value, HesitateSeconds, m.X, m.Y, m.Z, m.Yaw, m.Facing, sim.Config.YawRate));
            }
            _lastPhase = phase;
            // Past REGION3_X he is in region 3 (L2042, free movement only).
            if (freeStep && sim.Region == Dl05Lane.Region && sim.X > Dl05Lane.Region3X) sim.SetRegion(Dl05Lane.Region + 1);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            // Laid on the plate: he pats the sheet 1.6 s later (L4729–L4731).
            if (sim.Graph.Log.Has("dl05.body", MechanismEventKind.Event, (int)PushableEvent.Dock)) _patAt = sim.Clock + PatDelay;
            // updateCh1 (#7), after the weigh-in: the checkpoints (L4935–L4936), the label (L4940–L4944), bay (L4947).
            if (sim.Region == Dl05Lane.Region)
            {
                double x = sim.X;
                if (x > Dl05Scene.RationAt) sim.Checkpoints.Reach("ration");
                if (x > Dl05Scene.HatchAt) sim.Checkpoints.Reach("hatch");
                if (!LabelSeen && x > Dl05Scene.LabelX0 && x < Dl05Scene.LabelX1 && SceneQuirk.CanStart(sim))
                {
                    _save.MarkSeen(SeenLabel);
                    SceneQuirk.Start(sim, ClipNames.CheckLabel, cancel: true);
                }
                if (x > Dl05Scene.BayAt) sim.Checkpoints.Reach("bay");
            }
            // The pat's timeout, after the step: if (region 2 && !act && !hold) playQuirk('Pat') (L4731). As for a quirk
            // started in #7, the mixer has advanced its clip by a step when the next step's #4 reads it (L8502, L8510).
            if (PatDue(sim))
            {
                _patAt = double.NaN;
                if (sim.Region == Dl05Lane.Region && SceneQuirk.CanStart(sim)) SceneQuirk.Start(sim, "Pat", cancel: true);
            }
        }

        /// <summary>
        /// The prototype's push branch takes the nearest grip in reach, whichever way he faces (<c>nearUse</c>, L4251–L4255:
        /// <c>d &lt; best.d</c> in <c>PUSHABLES</c> order). U-11's resolver ranks targets in front of him first (#28, M7): at
        /// #10227, facing left between the body's grip 0.30 ahead and the drum's 0.15 behind, it takes the body. So each face
        /// here is available only while it is the nearest grip (<see cref="Pushable.CanStandAt"/> gets the asking face's
        /// stand point). Reads state only; never asks a face's <c>IsAvailable</c> (which calls this).
        /// </summary>
        private bool GripWins(ChapterSim sim, Pushable asking, double stand)
        {
            double x = sim.Motor.X, y = sim.Motor.Y, bestD = double.PositiveInfinity;
            IPushable best = null;
            for (int i = 0; i < _faces.Length; i++)
            {
                var f = _faces[i];
                var b = Base(f);
                if (b.State != PushableState.Free || Math.Abs(y - f.FloorY) >= 0.05) continue;               // state 'free'; L4254
                if (!double.IsNaN(b.Params.MinRoom) && !(b.Max - b.X > b.Params.MinRoom)) continue;            // avail, L4281
                double dx = x - (f.X - f.Side * f.Gap), d = Math.Abs(dx);
                if (d < (dx * f.Side < 0 ? f.BackReach : f.ForwardReach) && d < bestD) { best = f; bestD = d; }
            }
            if (best == null || !ReferenceEquals(Base(best), asking)) return false;
            return stand == asking.X - best.Side * asking.Gap;
        }

        private static Pushable Base(IPushable f) => f is PushTwin tw ? tw.Base : (Pushable)f;

        private static IPushable TwinOf(ChapterSim sim, Pushable p)
        {
            foreach (var it in sim.Resolver.Registered) if (it is PushTwin tw && ReferenceEquals(tw.Base, p)) return tw;
            throw new InvalidOperationException(p.Id + " has no twin registered.");
        }

        private bool IsBody(IInteractable t) => ReferenceEquals(t, _body) || (t is PushTwin tw && ReferenceEquals(tw.Base, _body));

        private bool PatDue(ChapterSim sim) => !double.IsNaN(_patAt) && sim.Clock >= _patAt - 1e-9;

    }

    /// <summary>
    /// He stands over the body before he takes hold of it the first time (<c>a.phase = 'hesitate'</c>, L4463–L4466): from the
    /// step after he arrives until <c>a.t &gt; 1.6</c>, still, turning only to his facing (<c>updateCharacter</c>). It owns his
    /// pose, so the motor (already in its Grab clip at time 0) is not stepped: the clip runs on from the next step, as the
    /// prototype's Grab starts on the step the hesitation ends (L4466).
    /// </summary>
    public sealed class Dl05HesitateAct : SceneAct
    {
        private readonly double _seconds, _yawRate;
        private readonly int _facing;

        public Dl05HesitateAct(string kind, double seconds, double x, double y, double z, double yaw, int facing, double yawRate)
            : base(kind, "Hesitate")
        {
            _seconds = seconds; _facing = facing; _yawRate = yawRate;
            X = x; Y = y; Z = z; Yaw = yaw;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                          // a.t += dt (L4390)
            Yaw = Smooth.MoveTowards(Yaw, _facing * Math.PI / 2, _yawRate * dt);
            return !(T > _seconds);                                           // L4466
        }
    }
}
