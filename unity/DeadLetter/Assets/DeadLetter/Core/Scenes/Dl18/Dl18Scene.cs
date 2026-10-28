using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Dl18
{
    /// <summary>
    /// DL-18 Room for One (docs/scenes/DL-18_room_for_one.md; chapter2_plan §4): up DL-17's stair onto ring A, past the
    /// sealed Works door and along the gallery into Mara's box room, where a fold bed and a fold bench on one frame share
    /// one space. Fold the bed away, pull the bench down to its stop, and climb bench (0.6) then sill (1.2) onto the terrace
    /// landing. Region 7 from the stair head (347.0) to DL-19 (361.0). No prototype: values cite the doc's sections.
    /// <para>Mechanisms: the leaves (<see cref="FoldingLeafParams.Dl18Bed"/>, <see cref="FoldingLeafParams.Dl18Bench"/>,
    /// built in U-10), which stop each other through their swept volumes (§3 "The two leaves") and wait for D-17 (no
    /// crushing). The lane is <see cref="Dl18Lane"/>. Everything else is <see cref="Dl18Rules"/>: the checkpoints, the
    /// Works door's chain and the two curiosities.</para>
    /// </summary>
    public static class Dl18Scene
    {
        public const string Id = "DL-18";

        /// <summary>The stair head (§3) to DL-19 (chapter2_plan §4).</summary>
        public const double X0 = Dl18Lane.StairHeadX, X1 = Dl18Lane.EndX;
        /// <summary>Checkpoints (§9, §11): <c>ring_a</c> on the gallery floor at the stair head, <c>terrace</c> on the landing at 1.2.</summary>
        public const double RingAX = 347.6, TerraceX = 355.8;

        /// <summary>The leaves (§11 <c>FoldBed</c>, <c>FoldBench</c>): the bed first, then the bench.</summary>
        public static readonly MechanismId Bed = "dl18.bed", Bench = "dl18.bench";

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "Room for One",
            X0 = X0, X1 = X1,
            Region = Dl18Lane.Region,                                                    // its checkpoints: ring_a, terrace (§9)
            Mechanisms = new[]
            {
                new MechanismDef(Bed, () => new FoldingLeaf(Bed, FoldingLeafParams.Dl18Bed())),
                new MechanismDef(Bench, () => new FoldingLeaf(Bench, FoldingLeafParams.Dl18Bench())),
            },
            Lane = Dl18Lane.Table,
            LaneContributors = Dl18Lane.Contributors,
            Rules = () => new Dl18Rules(),
        };
    }

    /// <summary>
    /// DL-18's rules. The checkpoints by position (§9): <c>ring_a</c> on the gallery floor from 347.6, <c>terrace</c> on the
    /// landing (1.2) from 355.8. Three things he can use that change nothing, each a <see cref="Station"/> the rules answer
    /// at Use when no mechanism does (the leaves always win), playing a <see cref="BeatAct"/> and its cues:
    /// <list type="bullet">
    /// <item>the Works door's chain (§2 "The sealed door", §11 <c>WorksDoor</c>): two tugs, a clank at each, nothing gives;</item>
    /// <item>the alarm clock (§6 curiosities, §11 <c>AlarmClock</c>): it rings 2 s; he startles, then stills it with a pat;</item>
    /// <item>the sketch (§6, §11 <c>Sketch</c>): a close look in the side view, 3 s, from the bench seat or the bed.</item>
    /// </list>
    /// The slide-off (§4, §10, §11 <c>FoldBench</c>: "not standable: any landing on it plays the slide-off"): a propped
    /// leaf is never ground in the lane (<see cref="FoldingLeafLane"/>), so he never lands on it; instead, whenever his body
    /// meets the propped bench's swept box while he moves freely (a jump or a mantle attempt at it from the bed, a fall,
    /// walking into it), <see cref="Dl18SlideAct"/> puts him up on its raised edge, rocks (cue <c>dl18.bench.rock</c>) and
    /// slides him back onto the bed with a soft bump (cue <c>dl18.bench.slide</c>), at rest at the strap within 1 s. No
    /// <c>Teeter</c>: nothing has given way, it was never level.
    /// </summary>
    public sealed class Dl18Rules : SceneRules
    {
        /// <summary>The chain through the door's handles (§3 Works door 347.4–348.6), used from the gallery floor.</summary>
        public static readonly Station Chain = new Station(standX: 348.0, reach: 0.4, face: 0);
        /// <summary>The alarm clock on its bracket at the bed's head (§3: 351.95, 0.5), from the floor or the bed (0.45).</summary>
        public static readonly Station Clock = new Station(standX: 351.95, reach: 0.3, face: 0, floorY: 0.45);
        /// <summary>The sketch over the bench (§3: 353.5–354.0, 1.1–1.45; §11 centre 353.75), from the bed (0.45) or the bench seat (0.6).</summary>
        public static readonly Station Sketch = new Station(standX: 353.75, reach: 0.3, face: 0, floorY: 0.6);
        /// <summary>Below this he is on the floor, out of the sketch's reach.</summary>
        public const double SketchFromY = 0.4;

        /// <summary>The acts' kinds (§11's object names) and phases.</summary>
        public static readonly ActId WorksDoor = ActId.Of("dl18.worksDoor"), AlarmClock = ActId.Of("dl18.alarmClock"), SketchKind = ActId.Of("dl18.sketch");
        public static readonly ActId Tug = ActIds.Clip(ClipNames.Tug), Startle = ActIds.Clip(ClipNames.Startle), Pat = ActIds.Clip("Pat"), Look = ActId.Of("Look");

        /// <summary>Cues: the chain clanks (and sheds dust) at each tug's click; the clock rings, then is stilled; the close look.</summary>
        public static readonly CueId ChainClank = CueId.Of("dl18.chain.clank"), ClockRing = CueId.Of("dl18.clock.ring"),
            ClockStill = CueId.Of("dl18.clock.still"), SketchLook = CueId.Of("dl18.sketch.look");

        /// <summary>The clock rings 2 s (§6); the sketch's look lasts 3 s (§6).</summary>
        public const double RingSeconds = 2.0, LookSeconds = 3.0;

        private static readonly BeatAct.Beat[] ChainBeats =
        {
            new BeatAct.Beat(Tug, QuirkAct.ClipSeconds(ClipNames.Tug), ChainClank, ClipTimings.TugEvents.Click / 24.0),
            new BeatAct.Beat(Tug, QuirkAct.ClipSeconds(ClipNames.Tug), ChainClank, ClipTimings.TugEvents.Click / 24.0),
        };

        private static readonly BeatAct.Beat[] ClockBeats =
        {
            new BeatAct.Beat(Startle, QuirkAct.ClipSeconds(ClipNames.Startle), ClockRing, 0),
            new BeatAct.Beat(Pat, QuirkAct.ClipSeconds("Pat"), ClockStill, RingSeconds - QuirkAct.ClipSeconds(ClipNames.Startle)),
        };

        private static readonly BeatAct.Beat[] SketchBeats = { new BeatAct.Beat(Look, LookSeconds, SketchLook, 0) };

        /// <summary>D-17's body as the leaves see it (<see cref="FoldingLeafParams"/>: half-width, heights, depth band).</summary>
        private static readonly FoldingLeafParams Body = FoldingLeafParams.Dl18Bench();
        /// <summary>Overlap beyond this is a contact.</summary>
        public const double ContactMargin = 1e-4;

        private bool _ringA, _terrace;
        private FoldingLeaf _bench;

        /// <summary>His body meets the propped bench's swept box at (x, y).</summary>
        public static bool MeetsPropped(FoldingLeaf bench, double x, double y, bool crouched)
        {
            if (bench.State != FoldingLeafState.Propped) return false;
            var body = SweptBox.Aligned(x - Body.BodyHalf, x + Body.BodyHalf, Body.BodyD0, Body.BodyD1, y, y + (crouched ? Body.CrouchHeight : Body.StandHeight));
            for (int i = 0, n = bench.VolumeCount; i < n; i++)
                if (SweptBox.Overlap(bench.Volume(i), body, ContactMargin)) return true;
            return false;
        }

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _bench = sim.Graph.Get<FoldingLeaf>(Dl18Scene.Bench);
            var cp = sim.Checkpoints.Current;
            _ringA = cp.Past("ring_a");
            _terrace = cp.Past("terrace");
        }

        /// <summary>Use at the chain, the clock or the sketch, when no mechanism answers there.</summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            if (!input.UsePressed || sim.Region != Dl18Lane.Region) return;
            var m = sim.Motor;
            if (m.IsActing || m.IsMantling || m.Hold != HoldKind.None || m.Ride != null || !m.Grounded || m.PreviewUse(out _)) return;
            var q = m.Query();
            BeatAct.Beat[] beats;
            ActId kind;
            if (Chain.Answers(q)) { kind = WorksDoor; beats = ChainBeats; }
            else if (Clock.Answers(q)) { kind = AlarmClock; beats = ClockBeats; }
            else if (Sketch.Answers(q) && q.Y >= SketchFromY) { kind = SketchKind; beats = SketchBeats; }
            else return;
            input.UsePressed = false;
            m.Stop();
            sim.StartAct(new BeatAct(kind, beats));
        }

        /// <summary>The slide-off off the propped bench; the checkpoints, by position after the step (§9).</summary>
        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Region != Dl18Lane.Region) return;
            double x = sim.X;
            if (!sim.Busy && MeetsPropped(_bench, x, sim.Y, sim.Motor.Crouched))
            {
                double back = Dl18SlideAct.BackX;
                sim.StartAct(new Dl18SlideAct(x, sim.Y, sim.Yaw, _bench, back, sim.Lane.SupportAt(back)));
                return;
            }
            if (!_ringA && x >= Dl18Scene.RingAX)
            {
                _ringA = true;
                sim.Checkpoints.Reach("ring_a");
            }
            if (!_terrace && x >= Dl18Scene.TerraceX && sim.Grounded && sim.Y >= Dl18Lane.LandingY - 1e-9)
            {
                _terrace = _ringA = true;
                sim.Checkpoints.Reach("terrace");
            }
        }
    }

    /// <summary>
    /// The slide-off (§4: "He mantles onto it; it rocks on the quilt and he slides back off onto the mattress with a soft
    /// bump"): up onto the propped bench's raised free edge (0.25 s), a rock there (0.3 s, cue <c>dl18.bench.rock</c>),
    /// then a slide back onto the bed with a soft bump (0.35 s, cue <c>dl18.bench.slide</c> as he slides). It owns his
    /// pose and hands him back at rest on the bed at <see cref="BackX"/>, where his body is clear of the bench and the
    /// strap answers, 0.9 s after the contact (§10: "within 1 s").
    /// </summary>
    public sealed class Dl18SlideAct : SceneAct
    {
        public const double ClimbSeconds = 0.25, RockSeconds = 0.3, SlideSeconds = 0.35;
        /// <summary>Where it leaves him: on the bed, his front 5 cm short of the bench (353.4) and within the strap's reach (353.15–353.75).</summary>
        public const double BackX = 353.18;

        public static readonly ActId SlideKind = ActId.Of(Dl18Scene.Bench), Climb = ActId.Of("Climb"), Rock = ActId.Of("Rock"), Slide = ActId.Of("Slide");
        public static readonly CueId RockCue = CueId.Of("dl18.bench.rock"), SlideCue = CueId.Of("dl18.bench.slide");

        private readonly double _x0, _y0, _ex, _ey, _bx, _by;
        private bool _rocked, _slid;

        public Dl18SlideAct(double x, double y, double yaw, FoldingLeaf bench, double backX, double backY) : base(SlideKind, Climb)
        {
            X = _x0 = x; Y = _y0 = y; Yaw = yaw;
            bench.FreeEdge(out _, out double edge);
            _ex = Math.Max(353.45, Math.Min(354.15, x));                                       // on the bench's length (353.4–354.2)
            _ey = edge;
            _bx = backX; _by = backY;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            if (T < ClimbSeconds)
            {
                double u = T / ClimbSeconds;
                X = _x0 + (_ex - _x0) * u;
                Y = _y0 + (_ey - _y0) * u;
                return true;
            }
            if (T < ClimbSeconds + RockSeconds)
            {
                X = _ex; Y = _ey;
                if (!_rocked) { _rocked = true; Phase = Rock; sim.Cue(RockCue); }
                return true;
            }
            if (!_slid) { _slid = true; Phase = Slide; sim.Cue(SlideCue); }
            double v = Math.Min(1, (T - ClimbSeconds - RockSeconds) / SlideSeconds);
            X = _ex + (_bx - _ex) * v;
            Y = _ey + (_by - _ey) * v;
            if (v < 1 - 1e-9) return true;
            sim.Motor.Place(_bx, _by, +1);
            return false;
        }
    }
}
