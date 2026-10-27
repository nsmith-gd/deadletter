using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl14
{
    /// <summary>
    /// DL-14 The Window (port_architecture §5; docs/chapter1_attendance_plan.md, the 23 Oct redesign): one crank, one chain,
    /// two blinds; whichever comes down, the other goes up, and each down blind folds a ledge out of the wall. The window
    /// pole left through A's chain wheel holds A up, so the first wind sends B down alone (and the panel behind it peels);
    /// out of the wheel, a wind swaps them; back in with A down, B comes down too, and the ledges climb to the hatch and the
    /// duct behind the wall. Region 6 from 232 to DL-14a at 248 (<c>sceneName</c>, L8136). Lines are index.html at 7b3c123
    /// (<c>ATT</c> L291–L294, <c>resetAtt</c> L5230, L5237–L5238, <c>nearAttItem</c>/<c>beginAtt</c>/<c>updateAttAct</c>
    /// L5282–L5304, L5318–L5324, L5364–L5376, <c>updateAtt</c> L5437–L5487, <c>updateAtt2Act</c> L5622–L5642).
    /// </summary>
    public static class Dl14Scene
    {
        public const string Id = "DL-14";

        public const double X0 = 232, X1 = 248;

        /// <summary><c>ATT.wheelA</c>, <c>ATT.wheelR</c> (L294): A's chain wheel and how near it he must be to use it; he stands 0.22 short (L5298).</summary>
        public const double WheelA = 235.0, WheelR = 0.25, WheelStand = WheelA - 0.22;
        /// <summary>The pole's only receiver (<see cref="ItemState.Placed"/> slot): through A's wheel.</summary>
        public const int JamSlot = 0;
        /// <summary>The <c>window</c> checkpoint on the floor past 234.6 (L5483).</summary>
        public const double WindowAt = 234.6;
        /// <summary>Into the duct: up at the hatch (y &gt; 2.1) between <c>hatch.x0 + 0.35</c> and <c>hatch.x1</c> (L5484).</summary>
        public const double DuctX0 = Dl14Lane.HatchX0 + 0.35, DuctX1 = Dl14Lane.HatchX1, DuctMinY = 2.1;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Window",
            X0 = X0, X1 = X1,
            Region = Dl14Lane.Region,                                                             // its checkpoints: window, hatch14
            // Step order = the prototype's: the pole moves and the jam is set or cleared in updatePlayer (#4); then updateAtt
            // winds the chain and runs the blinds, the ledges and the panel (#7, L5437–L5476).
            Mechanisms = new[]
            {
                new MechanismDef("dl14.pole", () => new CarriedItem("dl14.pole", PoleParams())),
                new MechanismDef("dl14.jam", () => new Dl14Jam("dl14.jam")),
                new MechanismDef("dl14.crank", () => new WindCrank("dl14.crank", WindCrankParams.Dl14Crank())),
                new MechanismDef("dl14.blinds", () => new PairedBlindDrive("dl14.blinds", BlindParams())),
            },
            Lane = Dl14Lane.Table,
            LaneContributors = Dl14Lane.Contributors,
            Rules = () => new Dl14Rules(),
        };

        /// <summary>
        /// The window pole (<c>game.att.pole</c>, L5230; <c>itemsHere</c> L4267: r 0.3, below 0.08, light): through A's
        /// wheel at every reset, never standable.
        /// </summary>
        public static CarriedItemParams PoleParams() => new CarriedItemParams
        {
            HomeX = WheelA, HomeBaseY = 0, HomeState = ItemState.Placed, HomeSlot = JamSlot,
            Radius = 0.3, Solid = false, BelowWrist = 0.08, IsLight = true,
        };

        /// <summary><see cref="PairedBlindParams.Dl14Blinds"/>, held by the jam (<c>s.jammed</c>, L5368), not by where the pole is.</summary>
        public static PairedBlindParams BlindParams()
        {
            var p = PairedBlindParams.Dl14Blinds();
            p.Hold = "dl14.jam";
            return p;
        }
    }

    /// <summary>
    /// The jam (<c>s.jammed</c>, L5240): the pole through A's wheel holds A wherever it is. Set at every reset; cleared as
    /// the pole is drawn out (Lift f16) and set as it goes back (SetDown f14). The acts ask for it, it changes at its next
    /// step (before the blinds wind, as the prototype's flag does in <c>updatePlayer</c>).
    /// </summary>
    public sealed class Dl14Jam : Mechanism, IEngageable
    {
        private bool _jammed, _set, _to;

        public Dl14Jam(MechanismId id) : base(id) { }

        public bool Engaged => _jammed;

        public void Set(bool jammed) { _set = true; _to = jammed; }

        public override void Reset(in Checkpoint cp) { _jammed = true; _set = false; Init(1); }       // jammed: true, L5240

        public override void Step(in StepContext ctx)
        {
            if (!_set) return;
            _set = false;
            _jammed = _to;
            Enter(ctx, _jammed ? 1 : 0);
        }

        protected override void WriteFields(ISnapshotWriter w) { w.WriteBool("jammed", _jammed); w.WriteBool("set", _set); w.WriteBool("to", _to); }
        protected override void ReadFields(ISnapshotReader r) { _jammed = r.ReadBool("jammed"); _set = r.ReadBool("set"); _to = r.ReadBool("to"); }
    }

    /// <summary>
    /// DL-14's rules: Use at A's wheel with the pole (<c>nearAttItem</c>, L5282–L5284: back in with it, or out with empty
    /// hands; never once past <c>hatch14</c>), the panel's <c>child</c> cue (L5474), the <c>window</c> checkpoint (L5483) and
    /// the way into the duct (L5484–L5487). <see cref="Always"/>: the wheel, the window and the duct are all in DL-14, but
    /// the duct takes him on into DL-14a; each trigger guards itself as the prototype does.
    /// </summary>
    public sealed class Dl14Rules : SceneRules
    {
        public static readonly CueId MusicChild = CueId.Of("music:child");
        private static readonly MechanismId BlindsId = "dl14.blinds";

        private CarriedItem _pole;
        private Dl14Jam _jam;
        private bool _duct;

        /// <summary>He has gone into the duct (<c>s.duct</c>; reset with <c>game.att</c>).</summary>
        public bool DuctTaken => _duct;

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _pole = sim.Graph.Get<CarriedItem>("dl14.pole");
            _jam = sim.Graph.Get<Dl14Jam>("dl14.jam");
            _duct = false;
        }

        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded || sim.Region != Dl14Lane.Region) return;
            bool atWheel = m.Y < 0.05 && Math.Abs(m.X - Dl14Scene.WheelA) < Dl14Scene.WheelR && !sim.Checkpoints.Current.Past("hatch14");   // L5282
            if (!atWheel) return;
            SceneAct act = null;
            if (m.Hold == HoldKind.Item && m.Carried == _pole && !_jam.Engaged) act = new JamPoleAct(sim, _pole, _jam);                     // L5283
            else if (m.Hold == HoldKind.None && _pole.State == ItemState.Placed && _pole.Slot == Dl14Scene.JamSlot) act = new UnjamPoleAct(sim, _pole, _jam);   // L5284
            if (act == null) return;
            input = MotorInput.None;
            sim.StartAct(act);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Graph.Log.Has(BlindsId, MechanismEventKind.Event, (int)PairedBlindEvent.Peel)) sim.Cue(MusicChild);   // L5474
            if (sim.Region != Dl14Lane.Region) return;
            double x = sim.X, y = sim.Y;
            if (x > Dl14Scene.WindowAt && y < 0.05) sim.Checkpoints.Reach("window");                                     // L5483
            if (x > Dl14Scene.DuctX0 && x < Dl14Scene.DuctX1 && y > Dl14Scene.DuctMinY && !_duct && !sim.Busy)              // L5484–L5487
            {
                _duct = true;
                sim.Checkpoints.Reach("hatch14");
                sim.StartAct(new DuctAct(sim));
            }
        }
    }

    /// <summary>
    /// He draws the pole back out of A's wheel (<c>'att:unjam'</c>, L5293–L5303): to 0.22 short of the wheel facing +1, Lift
    /// turned into the set; f16 the jam lets go, f22 the pole comes out at his x, f39 it is in his hands.
    /// </summary>
    public sealed class UnjamPoleAct : AttAct
    {
        public static readonly ActId Pole = ActId.Of("dl14.pole"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _pole;
        private readonly Dl14Jam _jam;
        private bool _freed, _taken;

        public UnjamPoleAct(ChapterSim sim, CarriedItem pole, Dl14Jam jam) : base(sim, Pole, Dl14Scene.WheelStand, 1) { _pole = pole; _jam = jam; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Lift; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 16 && !_freed) { _freed = true; _jam.Set(false); }                                                 // L5297
            if (f >= 22 && !_taken) { _taken = true; _pole.MoveTo(ItemState.Carried, X, _pole.BaseY); }                  // L5299
            if (!(f >= 39)) return true;
            Take(_pole);                                                                                                  // L5303
            return false;
        }
    }

    /// <summary>
    /// He puts the pole back through A's wheel (<c>'att:jam'</c>, L5316, L5318–L5324): to 0.22 short of the wheel facing +1,
    /// SetDown turned into the set; f14 it is through the wheel, jammed, and his hands are empty; f35 he is done.
    /// </summary>
    public sealed class JamPoleAct : AttAct
    {
        public static readonly ActId Wheel = ActId.Of("dl14.wheel"), SetDown = ActIds.Clip(ClipNames.SetDown);
        private readonly CarriedItem _pole;
        private readonly Dl14Jam _jam;
        private bool _jammed;

        public JamPoleAct(ChapterSim sim, CarriedItem pole, Dl14Jam jam) : base(sim, Wheel, Dl14Scene.WheelStand, 1) { _pole = pole; _jam = jam; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = SetDown; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 14 && !_jammed)
            {
                _jammed = true;
                _pole.MoveTo(ItemState.Placed, _pole.X, _pole.BaseY, Dl14Scene.JamSlot);
                _jam.Set(true);
                LetGo();
            }
            return !(f >= 35);
        }
    }

    /// <summary>
    /// Through the hatch and along the duct behind the wall (<c>'duct'</c>, L5622–L5642): he steps into the wall at 0.7 m/s
    /// to its depth (turned into the set), turns along it and crawls on at 1.9 m/s, coming down from 2.15 to 1.15 as it
    /// runs from 241 to 248, to its end over bunk 1 (248.95), then steps out to the lane facing the camera, at
    /// <c>dorm</c>. Started by the rules after the mechanisms (<c>updateAtt</c>, L5486), so its first step is the next.
    /// </summary>
    public sealed class DuctAct : SceneAct
    {
        public static readonly ActId Hatch = ActId.Of("dl14.hatch"), In = ActId.Of("In"), Along = ActId.Of("Along"), Out = ActId.Of("Out");
        /// <summary><c>ATT2.duct</c> (L5516): its end, its heights, its depth (Unity +, three −1.3) and where it starts to fall.</summary>
        public const double DuctEndX = 248.95, H0 = 2.15, H1 = 1.15, DuctZ = 1.3, FallX0 = 241, FallLength = 7;
        public const double StepSpeed = 0.7, CrawlSpeed = 1.9;

        private readonly ChapterSim _sim;
        private readonly double _yawRate;
        private double _override;
        private bool _hasOverride;
        private int _facing;

        public DuctAct(ChapterSim sim) : base(Hatch, In)
        {
            _sim = sim;
            X = sim.X; Y = sim.Y; Z = sim.Z; Yaw = sim.Yaw;
            _facing = sim.Motor.Facing;
            _yawRate = sim.Config.YawRate;
        }

        public override bool OwnsPose => true;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            bool keep = true;
            T += dt;
            if (Phase == In)
            {
                _hasOverride = true; _override = Math.PI;                                                     // L5626
                Z = Math.Min(DuctZ, Z + StepSpeed * dt);                                                       // three: max(D.z, z − 0.7·dt)
                if (Z >= DuctZ - 1e-3) { Phase = Along; _override = Math.PI / 2; }                             // L5628
            }
            else if (Phase == Along)
            {
                X = Math.Min(DuctEndX, X + CrawlSpeed * dt);                                                   // L5630
                double t = Smooth.Step((X - FallX0) / FallLength);
                Y = (1 - t) * H0 + t * H1;                                                                     // THREE.MathUtils.lerp, L5631
                if (X >= DuctEndX) { Phase = Out; _facing = 1; }                                               // L5633
            }
            else
            {
                _hasOverride = true; _override = 0;                                                            // L5635
                Z = Math.Max(0, Z - StepSpeed * dt);
                if (Z <= 1e-3)                                                                                 // L5636–L5640
                {
                    Z = 0; keep = false; _hasOverride = false;
                    sim.Checkpoints.Reach("dorm");
                }
            }
            double target = _hasOverride ? _override : (_facing > 0 ? Math.PI / 2 : -Math.PI / 2);
            Yaw = Smooth.MoveTowards(Yaw, target, _yawRate * dt);
            if (!keep) sim.Motor.Place(X, Y, _facing, Yaw);
            return keep;
        }
    }
}
