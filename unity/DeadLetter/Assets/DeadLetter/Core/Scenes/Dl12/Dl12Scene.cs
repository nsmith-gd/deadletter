using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl12
{
    /// <summary>
    /// DL-12 Coats Without Children (port_architecture §5; docs/chapter1_attendance_plan.md, the 23 Oct redesign): the
    /// register gate opens while someone stands on the strip AND coat 7 hangs on peg 7. The coat waits on the front of the
    /// lost-property bin; peg 7 is out of reach from the floor, so he steps up onto the bench; then the stand-in figure,
    /// pushed onto the strip, keeps the gate open for him. Region 6 from the arrival door to DL-13 at 216
    /// (<c>sceneName</c>, L8136). Lines are index.html at 7b3c123 (<c>ATT</c> L286–L296, <c>resetAtt</c> L5228,
    /// <c>nearAttItem</c>/<c>beginAtt</c>/<c>updateAttAct</c> L5275–L5318, <c>updateAtt</c> L5381–L5408, L5481).
    /// </summary>
    public static class Dl12Scene
    {
        public const string Id = "DL-12";

        /// <summary><c>OFF6</c> (L285): region 6's origin; DL-12 is the region's first scene, so it also holds everything left of it.</summary>
        public const double X0 = 200;
        /// <summary>DL-13 begins at x ≥ 216 (L8136).</summary>
        public const double X1 = 216;

        /// <summary><c>ATT.coat0</c> (L287) and <c>ATT_COAT_BIN</c> (L5509): coat 7 hangs on the front of the bin.</summary>
        public const double Coat0 = 202.92, BinX = 202.92, BinY = 0.98;
        /// <summary>Taken off the bin it rests (for the set-down's drop) at the bin's height less 0.45 (L5302).</summary>
        public const double CoatHeldBase = BinY - 0.45;
        /// <summary><c>ATT.peg.x</c> (L287).</summary>
        public const double PegX = 205.4;
        /// <summary>The coat's two receivers (<see cref="ItemState.Placed"/> slots): the bin and peg 7.</summary>
        public const int BinSlot = 0, PegSlot = 1;
        /// <summary><c>ATT.fig</c> (L288): the stand-in figure's start and the strip's centre; its travel from <c>bench.x1 + 0.75</c> (L4283).</summary>
        public const double Fig0 = 207.0, FigStrip = 208.4, FigMin = Dl12Lane.BenchX1 + 0.75;
        /// <summary>The <c>register</c> checkpoint past <c>ATT.gate.x + 0.6</c> (L5481).</summary>
        public const double RegisterAt = Dl12Lane.GateX + 0.6;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "Coats Without Children",
            X0 = X0, X1 = X1,
            Region = Dl12Lane.Region,                                                          // its checkpoints: school, register
            // Step order = the prototype's: updatePlayer moves the coat and the figure (#4), then updateAtt weighs the strip
            // and moves the gate (#7, L5381–L5406).
            Mechanisms = new[]
            {
                new MechanismDef("dl12.coat", () => new CarriedItem("dl12.coat", CoatParams())),
                new MechanismDef("dl12.peg", () => new Dl12Peg("dl12.peg")),
                new MechanismDef("dl12.figure", () => new Pushable("dl12.figure", FigureParams())),
                new MechanismDef("dl12.strip", () => new PresenceStrip("dl12.strip", StripParams())),
                new MechanismDef("dl12.gate", () => new FollowerActuator("dl12.gate", FollowerParams.Dl12Gate())),
            },
            Interactables = g => new IInteractable[] { new PushTwin(g.Get<Pushable>("dl12.figure")) },   // figAlt, L4291–L4294
            Lane = Dl12Lane.Table,
            LaneContributors = Dl12Lane.Contributors,
            Rules = () => new Dl12Rules(),
        };

        /// <summary>
        /// Coat 7 (<c>game.att.coat</c>, L5229; <c>itemsHere</c> L4266: r 0.16, below 0.16, light): on the bin at the start
        /// (a receiver's slot), on peg 7 from <c>register</c>; never standable. Its x and base stay <c>coat0</c> and 0 when
        /// reset (L5229) and are the bin's when he takes it (L5302).
        /// </summary>
        public static CarriedItemParams CoatParams() => new CarriedItemParams
        {
            HomeX = Coat0, HomeBaseY = 0, HomeState = ItemState.Placed, HomeSlot = BinSlot,
            Radius = 0.16, Solid = false, BelowWrist = 0.16, IsLight = true,
            MovedAfter = "register", MovedState = ItemState.Placed, MovedX = Coat0, MovedBaseY = 0, MovedSlot = PegSlot,
        };

        /// <summary>
        /// The stand-in figure (<c>PUSHABLES.fig</c>, L4283): pushed from its left (gap 0.6) at 0.4 m/s from 206.65 to the
        /// strip's centre 208.4, where he lets go and it stays free; on the strip from <c>register</c> (L5233); the other
        /// face is <c>figAlt</c> (L4291). Not on the lane.
        /// </summary>
        public static PushableParams FigureParams() => new PushableParams
        {
            StartX = Fig0, ParkedAfter = "register", ParkedX = FigStrip, ParkedState = PushableState.Free,
            Side = +1, Gap = 0.6, Speed = 0.4, Accel = 1.4,
            Min = FigMin, Max = FigStrip,
            FloorY = 0, Z = 0, ForwardReach = 0.34, BackReach = 0.34,
        };

        /// <summary>The register strip (<see cref="PresenceStripParams.Dl12Strip"/>), its coat read off peg 7 (<see cref="Dl12Peg"/>).</summary>
        public static PresenceStripParams StripParams()
        {
            var p = PresenceStripParams.Dl12Strip();
            p.Coat = "dl12.peg";
            return p;
        }
    }

    /// <summary>
    /// Peg 7 (<c>dl12.peg</c>): coat 7 on it, as the register strip weighs it (<c>coat = s.coat.state === 'peg'</c>,
    /// L5383): <see cref="BodySupport.Placed"/> while the coat hangs in its peg slot, else away. It has no state of its
    /// own; it reads the coat as it is this step (the coat steps first).
    /// </summary>
    public sealed class Dl12Peg : Mechanism, IPlateBody
    {
        private CarriedItem _coat;

        public Dl12Peg(MechanismId id) : base(id) { }

        public bool HasCoat => _coat != null && _coat.State == ItemState.Placed && _coat.Slot == Dl12Scene.PegSlot;
        public double X => Dl12Scene.PegX;
        public double SupportX => Dl12Scene.PegX;
        public BodySupport Support => HasCoat ? BodySupport.Placed : BodySupport.Away;

        public override void Link(MechanismLinker link) => _coat = link.Read<CarriedItem>("dl12.coat")
            ?? throw new InvalidOperationException(Id + " needs dl12.coat.");

        public override void Reset(in Checkpoint cp) => Init(0);
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }

    /// <summary>
    /// DL-12's rules: Use with coat 7 (<c>nearAttItem</c>, L5275–L5284, which the prototype asks before anything else in
    /// region 6, L4206): off the bin, onto peg 7 from the bench, or a reach for it from the floor; the register's voice
    /// (<see cref="PresenceStrip"/>'s events, L5384–L5391); and the <c>register</c> checkpoint (L5481).
    /// </summary>
    public sealed class Dl12Rules : SceneRules
    {
        public static readonly CueId SoundPlate = CueId.Of("sound:plate"), VoiceGate1 = CueId.Of("voice:att_gate_1"),
            VoiceGate2 = CueId.Of("voice:att_gate_2"), VoiceGate3 = CueId.Of("voice:att_gate_3");

        private static readonly MechanismId StripId = "dl12.strip";
        private CarriedItem _coat;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening) => _coat = sim.Graph.Get<CarriedItem>("dl12.coat");

        /// <summary>
        /// <c>nearAttItem</c>'s coat answers (L5277–L5281), ahead of the motor's resolver: on the ground, out of any act or
        /// ride. Off the bin (hands empty, on the floor within 0.35 of it), onto peg 7 (carrying it, on the bench within
        /// 0.4 of the peg), or reaching for the peg from the floor beside the bench (within 0.45 of either end).
        /// </summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded) return;
            double x = m.X, y = m.Y;
            SceneAct act = null;
            if (m.Hold == HoldKind.None && _coat.State == ItemState.Placed && _coat.Slot == Dl12Scene.BinSlot && y < 0.05 && Math.Abs(x - Dl12Scene.Coat0) < 0.35)
                act = new CoatLiftAct(sim, _coat);
            else if (m.Hold == HoldKind.Item && m.Carried == _coat && Math.Abs(y - Dl12Lane.BenchH) < 0.05 && Math.Abs(x - Dl12Scene.PegX) < 0.4)
                act = new HangCoatAct(sim, _coat);
            else if (m.Hold == HoldKind.Item && m.Carried == _coat && y < 0.05 && x > Dl12Lane.BenchX0 - 0.45 && x < Dl12Lane.BenchX1 + 0.45)
                act = new ReachPegAct(sim, _coat);
            if (act == null) return;
            input = MotorInput.None;
            sim.StartAct(act);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            for (int i = 0; i < log.Count; i++)
            {
                var e = log[i];
                if (e.Id != StripId || e.Kind != MechanismEventKind.Event) continue;
                switch ((PresenceEvent)e.Code)
                {
                    case PresenceEvent.Press: sim.Cue(SoundPlate); break;                                   // L5384
                    case PresenceEvent.AskForCoat: sim.Cue(e.Index > 1 ? VoiceGate2 : VoiceGate1); break;   // L5387–L5390
                    case PresenceEvent.Thanks: sim.Cue(VoiceGate3); break;                                  // L5391
                }
            }
            if (sim.Region == Dl12Lane.Region && sim.X > Dl12Scene.RegisterAt) sim.Checkpoints.Reach("register");   // L5481
        }
    }

    /// <summary>
    /// He takes coat 7 off the bin (<c>'att:coat'</c>, L5293–L5303): to <c>coat0</c> facing +1, then Lift turned into the
    /// set; f13 a lift sound, f22 it leaves the bin (at the bin's x, its base 0.45 below the bin), f39 it is in his hands.
    /// </summary>
    public sealed class CoatLiftAct : AttAct
    {
        public static readonly ActId Coat = ActId.Of("dl12.coat"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _coat;
        private bool _taken;

        public CoatLiftAct(ChapterSim sim, CarriedItem coat) : base(sim, Coat, Dl12Scene.Coat0, 1) { _coat = coat; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Lift; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 22 && !_taken) { _taken = true; _coat.MoveTo(ItemState.Carried, Dl12Scene.BinX, Dl12Scene.CoatHeldBase); }
            return !(f >= 39);
        }

        protected override void OnEnd()
        {
            base.OnEnd();
            Sim.Motor.TakeItem(_coat);
        }
    }

    /// <summary>
    /// He hangs coat 7 on peg 7 from the bench (<c>'att:hang'</c>, L5314, L5318–L5324): to the peg facing +1, SetDownHigh
    /// turned into the set; f14 it is on the peg and his hands are empty, f35 he is done.
    /// </summary>
    public sealed class HangCoatAct : AttAct
    {
        public static readonly ActId Peg = ActId.Of("dl12.peg"), SetDownHigh = ActIds.Clip(ClipNames.SetDownHigh);
        private readonly CarriedItem _coat;
        private bool _hung;

        public HangCoatAct(ChapterSim sim, CarriedItem coat) : base(sim, Peg, Dl12Scene.PegX, 1) { _coat = coat; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = SetDownHigh; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 14 && !_hung)
            {
                _hung = true;
                _coat.MoveTo(ItemState.Placed, _coat.X, _coat.BaseY, Dl12Scene.PegSlot);
                LetGo();
            }
            return !(f >= 35);
        }
    }

    /// <summary>
    /// From the floor beside the bench with coat 7 he reaches up for peg 7 and cannot (<c>'att:reachpeg'</c>, L5306–L5311,
    /// the 22 Oct playtest): no approach; he faces the peg, holds the coat up (Present) for 1.1 s and looks along the bench
    /// until 2.2 s, still carrying it.
    /// </summary>
    public sealed class ReachPegAct : AttAct
    {
        public static readonly ActId Reach = ActId.Of("dl12.reachPeg"), Present = ActIds.Clip(ClipNames.Present);
        private readonly CarriedItem _coat;

        public ReachPegAct(ChapterSim sim, CarriedItem coat) : base(sim, Reach, double.NaN, 0) { _coat = coat; Phase = Present; }

        protected override void OnArrive() { }

        protected override bool OnClip(double dt)
        {
            if (T < 0.02) { int s = Math.Sign(Dl12Scene.PegX - X); Facing = s != 0 ? s : 1; }   // L5308
            return !(T > 2.2);                                                                       // L5310
        }

        protected override void OnEnd()
        {
            base.OnEnd();
            Sim.Motor.TakeItem(_coat);
        }
    }
}
