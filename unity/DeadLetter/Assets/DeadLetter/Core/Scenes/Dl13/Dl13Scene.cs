using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Push;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl13
{
    /// <summary>
    /// DL-13 The Repeated Lesson (port_architecture §5; docs/chapter1_attendance_plan.md): a pupil in the front seat starts
    /// the recorded lesson, 12 s round; its three steps fold out of the wall in turn and fold away again, never all at once.
    /// The second stand-in figure, pushed into the seat, starts it; the brake, pulled in the moment all three are out, holds
    /// them there, and he climbs to the gallery. Region 6 from 216 to DL-14 at 232 (<c>sceneName</c>, L8136). Lines are
    /// index.html at 7b3c123 (<c>ATT</c> L289–L291, <c>resetAtt</c> L5234–L5236, <c>nearAttFixed</c> L5286–L5290,
    /// <c>updateAttAct</c> L5344–L5363, <c>updateAtt</c> L5409–L5436, L5482).
    /// </summary>
    public static class Dl13Scene
    {
        public const string Id = "DL-13";

        public const double X0 = 216, X1 = 232;

        /// <summary><c>ATT.fig2</c> (L289): the second figure's start and the front seat; its travel from 217.3 (L4284).</summary>
        public const double Fig0 = 217.6, Seat = 219.40, FigMin = 217.3;
        /// <summary>Seated within 0.06 of the seat (L5410).</summary>
        public const double SeatedWithin = 0.06;
        /// <summary>The <c>lesson</c> checkpoint past 216.6 (L5482); <c>gallery13</c> up on the gallery (y &gt; 2.0, L5436).</summary>
        public const double LessonAt = 216.6, GalleryY = 2.0;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Repeated Lesson",
            X0 = X0, X1 = X1,
            Region = Dl13Lane.Region,                                                             // its checkpoints: lesson, gallery13
            // Step order = the prototype's: the figure moves and the brake drops in updatePlayer (#4), then updateAtt seats the
            // figure and runs the lesson (#7, L5409–L5428).
            Mechanisms = new[]
            {
                new MechanismDef("dl13.figure", () => new Pushable("dl13.figure", FigureParams())),
                new MechanismDef("dl13.seat", () => new Dl13Seat("dl13.seat")),
                new MechanismDef("dl13.brake", () => new CycleBrake("dl13.brake", CycleBrakeParams.Dl13Brake())),
                new MechanismDef("dl13.lesson", () => new CycleClock("dl13.lesson", CycleClockParams.Dl13Lesson())),
            },
            Interactables = g => new IInteractable[] { new PushTwin(g.Get<Pushable>("dl13.figure")) },   // fig2Alt, L4291–L4294
            Lane = Dl13Lane.Table,
            LaneContributors = Dl13Lane.Contributors,
            Rules = () => new Dl13Rules(),
        };

        /// <summary>
        /// The second figure (<c>PUSHABLES.fig2</c>, L4284): pushed from its left (gap 0.6) at 0.4 m/s from 217.3 to the
        /// front seat 219.4, where he lets go; in the seat from <c>gallery13</c> (L5234); the twin is <c>fig2Alt</c>.
        /// </summary>
        public static PushableParams FigureParams() => new PushableParams
        {
            StartX = Fig0, ParkedAfter = "gallery13", ParkedX = Seat, ParkedState = PushableState.Free,
            Side = +1, Gap = 0.6, Speed = 0.4, Accel = 1.4,
            Min = FigMin, Max = Seat,
            FloorY = 0, Z = 0, ForwardReach = 0.34, BackReach = 0.34,
        };
    }

    /// <summary>
    /// The front seat (<c>dl13.seat</c>): engaged while the second figure sits in it, within 0.06 of 219.40
    /// (<c>seated</c>, L5410). The lesson's gate. It has no state of its own; it reads the figure as it is this step.
    /// </summary>
    public sealed class Dl13Seat : Mechanism, IEngageable
    {
        private Pushable _fig;

        public Dl13Seat(MechanismId id) : base(id) { }

        public bool Engaged => _fig != null && Math.Abs(_fig.X - Dl13Scene.Seat) < Dl13Scene.SeatedWithin;

        public override void Link(MechanismLinker link) => _fig = link.Read<Pushable>("dl13.figure")
            ?? throw new InvalidOperationException(Id + " needs dl13.figure.");

        public override void Reset(in Checkpoint cp) => Init(0);
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }

    /// <summary>
    /// DL-13's rules: the lesson's bell (<see cref="CycleClockEvent.Started"/>, L5411) and the checkpoints <c>lesson</c>
    /// (L5482) and <c>gallery13</c> (L5436). <see cref="Always"/>: the gallery runs on past 232 into DL-14 (to the stair at
    /// 233), and the prototype reaches <c>gallery13</c> anywhere up there; each trigger guards itself by region and x.
    /// </summary>
    public sealed class Dl13Rules : SceneRules
    {
        public static readonly CueId SoundBell = CueId.Of("sound:bell");
        private static readonly MechanismId LessonId = "dl13.lesson";

        public override bool Always => true;

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Graph.Log.Has(LessonId, MechanismEventKind.Event, (int)CycleClockEvent.Started)) sim.Cue(SoundBell);
            if (sim.Region != Dl13Lane.Region) return;
            double x = sim.X;
            if (sim.Y > Dl13Scene.GalleryY && x > Dl13Lane.GalleryX0 && x < Dl13Lane.StairX0) sim.Checkpoints.Reach("gallery13");   // L5436
            if (x > Dl13Scene.LessonAt) sim.Checkpoints.Reach("lesson");                                                                                         // L5482
        }
    }
}
