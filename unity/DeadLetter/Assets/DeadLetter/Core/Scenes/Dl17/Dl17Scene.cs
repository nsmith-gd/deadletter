using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Water;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl17
{
    /// <summary>
    /// DL-17 A Different Lesson (port_architecture §5; docs/chapter1_part2_plan.md, rev 0.3 and the expansion's test rig):
    /// the workshop. He lifts the wedged tray off the plan chest, pulls its drawer and reads her drawing and her placement
    /// (the records scan themselves); his label is forwarded again, to ring A. Her drawing explains the rig: with only the
    /// sluice to bed 1 open, a full tank's run lifts bed 1's float, its latch, and the stair door up to ring A opens; he
    /// leaves the school by it. Region 6 from 324 to the end of the school (<c>sceneName</c>, L8136). Lines are index.html at
    /// 7b3c123 (<c>ATT2</c> L5529–L5531, <c>resetAtt2</c> L5553, <c>resetAtt3</c> L5923, <c>nearAtt2Item</c>/<c>Fixed</c>
    /// L5614–L5627, <c>updateAtt2Act</c> L5657–L5708, <c>updateAtt2</c> L5773–L5794, L5803, <c>placeTray17</c> L5856–L5862,
    /// <c>updateAtt3Act</c> L6193–L6208, <c>updateAtt3</c> L6247–L6259, <c>finishAtt</c> L6461–L6469).
    /// </summary>
    public static class Dl17Scene
    {
        public const string Id = "DL-17";

        /// <summary>DL-17 runs to the end of the school; the chapter ends when he leaves by the stair (<see cref="Dl17Rules.HasLeft"/>).</summary>
        public const double X0 = 324, X1 = Dl12Lane.Right;

        /// <summary><c>ATT2.tray0</c> (L5529): the tray wedged on the plan chest; he stands 0.15 short, within 0.25 (L5615, L5630).</summary>
        public const double Tray0 = 329.7, TrayStand = Tray0 - 0.15, TrayReach = 0.25;
        /// <summary>Set down in front of the drawer, it is moved aside to the bench leg (<c>trayKeepOut</c>, <c>trayPark</c>, L5529, L5858).</summary>
        public const double KeepOutX0 = 329.15, KeepOutX1 = 330.85, TrayPark = 328.7;
        /// <summary><c>ATT2.drawer.x</c> (L5529): the drawer, within 0.3; he reads it 0.65 aside, for the close-up (L5626–L5630).</summary>
        public const double DrawerX = 330.0, DrawerReach = 0.3, ReadStand = DrawerX - 0.65;
        /// <summary>The tray's receiver (<see cref="ItemState.Placed"/> slot): wedged on the plan chest.</summary>
        public const int WedgedSlot = 0;
        /// <summary>The <c>workshop</c> checkpoint past 324.6 (L5803); the end, past <c>door17.landing + 0.12</c> (L5793).</summary>
        public const double WorkshopAt = 324.6, EndAt = 341.1 + 0.12;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "A Different Lesson",
            X0 = X0, X1 = X1,
            Region = Dl17Lane.Region,                                                             // its checkpoint: workshop
            // Step order = the prototype's: the tray, the valve and the sluices move in updatePlayer (#4); updateAtt2 slides
            // the drawer out (#7, L5785) and opens the stair door (L5789–L5794), updateAtt3 runs the rig and its float latch
            // after (L6247–L6259). The door steps after the latch so its delay starts on the latch's step (latchAt).
            Mechanisms = new[]
            {
                new MechanismDef("dl17.tray", () => new CarriedItem("dl17.tray", TrayParams())),
                new MechanismDef("dl17.drawer", () => new Dl17Drawer("dl17.drawer")),
                new MechanismDef("dl17.valve", () => new SluiceValve("dl17.valve", SluiceValveParams.Dl17Valve())),
                new MechanismDef("dl17.sluiceA", () => new Sluice("dl17.sluiceA", SluiceParams.Dl17Sluice(0))),
                new MechanismDef("dl17.sluiceB", () => new Sluice("dl17.sluiceB", SluiceParams.Dl17Sluice(1))),
                new MechanismDef("dl17.sluiceC", () => new Sluice("dl17.sluiceC", SluiceParams.Dl17Sluice(2))),
                new MechanismDef("dl17.rig", () => new SluiceRig("dl17.rig", SluiceRigParams.Dl17Rig())),
                new MechanismDef("dl17.latch", () => new FloatLatch("dl17.latch", FloatLatchParams.Dl17Latch())),
                new MechanismDef("dl17.stairDoor", () => new Door("dl17.stairDoor", DoorParams.Dl17StairDoor())),
            },
            Lane = Dl17Lane.Table,
            LaneContributors = Dl17Lane.Contributors,
            Rules = () => new Dl17Rules(),
        };

        /// <summary>
        /// The tray (<c>f17.tray</c>, L5553; <c>itemsHere</c> L4268: r 0.21, below 0.12, heavy): wedged on the plan chest at
        /// every reset, never standable.
        /// </summary>
        public static CarriedItemParams TrayParams() => new CarriedItemParams
        {
            HomeX = Tray0, HomeBaseY = 0, HomeState = ItemState.Placed, HomeSlot = WedgedSlot,
            Radius = 0.21, Solid = false, BelowWrist = 0.12, IsLight = false,
        };
    }

    /// <summary>
    /// The plan chest's drawer (<c>f17.drawer</c>, L5553, L5785): pulled, it slides out over 1.1 s. Signals:
    /// <see cref="Position"/> = how far out, 0..1.
    /// </summary>
    public sealed class Dl17Drawer : Mechanism, IPositionSource
    {
        public const double SlideTime = 1.1;
        private bool _pulling, _pull;

        public Dl17Drawer(MechanismId id) : base(id) { }

        public double Position { get; private set; }

        /// <summary>The pull, 0.35 s into it (L5697): it slides from its next step.</summary>
        public void Pull() => _pull = true;

        public override void Reset(in Checkpoint cp) { Position = 0; _pulling = _pull = false; Init(0); }

        public override void Step(in StepContext ctx)
        {
            if (_pull) { _pull = false; _pulling = true; }
            if (_pulling && Position < 1) Position = Math.Min(1, Position + ctx.Dt / SlideTime);                  // L5785
            Enter(ctx, Position >= 1 ? 2 : _pulling ? 1 : 0);
        }

        protected override void WriteFields(ISnapshotWriter w) { w.WriteDouble("out", Position); w.WriteBool("pulling", _pulling); w.WriteBool("pull", _pull); }
        protected override void ReadFields(ISnapshotReader r) { Position = r.ReadDouble("out"); _pulling = r.ReadBool("pulling"); _pull = r.ReadBool("pull"); }
    }

    /// <summary>
    /// DL-17's rules: Use at the plan chest (<c>nearAtt2Item</c>: the tray off it, L5615, asked first; <c>nearAtt2Fixed</c>:
    /// the drawer, then reading it, L5626–L5627), the tray moved aside from in front of the drawer (L5858), her drawing
    /// read (the T-key, the drawer-read flag the stair door waits for), his label checked 0.3 s after (L5778), the
    /// <c>workshop</c> checkpoint (L5803) and the end by the stair (L5793): <see cref="HasLeft"/>.
    /// </summary>
    public sealed class Dl17Rules : SceneRules
    {
        public static readonly CueId VoiceVolunteer = CueId.Of("voice:att_volunteer"), MusicEnd = CueId.Of("music:endAtt");
        /// <summary>He checks his label 0.3 s after reading (<c>t &gt; 0.3</c>, L5778) and holds it 2.2 s (<c>holdFor</c>).</summary>
        public const double CheckAfter = 0.3, CheckHold = 2.2;

        private CarriedItem _tray;
        private Dl17Drawer _drawer;
        private bool _read, _checked, _ended;
        private double _readDone;

        /// <summary>Her drawing read (<c>d.read</c>, reset with the chapter's state, L5553), the T-key his (<c>d.key</c>).</summary>
        public bool Read => _read;
        /// <summary>He has left the school by the stair (<c>s.ended</c>).</summary>
        public bool Ended => _ended;

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _tray = sim.Graph.Get<CarriedItem>("dl17.tray"); _drawer = sim.Graph.Get<Dl17Drawer>("dl17.drawer");
            _read = _checked = _ended = false; _readDone = double.NaN;
        }

        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded || m.Hold != HoldKind.None || sim.Region != Dl17Lane.Region) return;
            double x = m.X, y = m.Y;
            SceneAct act = null;
            bool fixedFirst = false;
            if (_tray.State == ItemState.Placed && y < 0.05 && Math.Abs(x - Dl17Scene.TrayStand) < Dl17Scene.TrayReach) act = new TrayLiftAct(sim, _tray);   // L5615
            else if (!(y > 0.05) && Math.Abs(x - Dl17Scene.DrawerX) < Dl17Scene.DrawerReach)
            {
                fixedFirst = true;
                if (_tray.State != ItemState.Placed && _drawer.Position == 0) act = new DrawerAct(sim, _drawer);                                         // L5626
                else if (_drawer.Position >= 1 && !_read) act = new ReadAct(sim, this);                                                                 // L5627
            }
            if (act == null) return;
            if (fixedFirst && m.PreviewUse(out var c) && c.Category < InteractionCategory.Fixed) return;
            input = MotorInput.None;
            sim.StartAct(act);
        }

        /// <summary>The read act's end (L5702–L5706): read, the T-key, and the flag the stair door waits for.</summary>
        internal void OnRead(ChapterSim sim)
        {
            _read = true; _readDone = sim.Clock;
            sim.Checkpoints.SetFlag(StoryFlags.Dl17DrawerRead);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Region != Dl17Lane.Region) return;
            // Put down in front of the drawer, it is set aside by the bench leg once it has landed (L5858).
            if (_tray.State == ItemState.Floor && _tray.X > Dl17Scene.KeepOutX0 && _tray.X < Dl17Scene.KeepOutX1 && _tray.SinceSetDown >= CarriedItem.DropSeconds)
                _tray.MoveTo(ItemState.Floor, Dl17Scene.TrayPark, _tray.BaseY);
            if (_read && !_ended)                                                                                  // L5776–L5794
            {
                double t = sim.Clock - _readDone;
                if (t > CheckAfter && !_checked && !sim.Busy)
                {
                    _checked = true;
                    if (SceneQuirk.CanStart(sim))
                    {
                        SceneQuirk.Stop(sim);
                        sim.StartAct(new QuirkAct(ClipNames.CheckLabel, QuirkAct.ClipSeconds(ClipNames.CheckLabel), false, sim.Clock, holdFor: CheckHold));
                    }
                }
                if (sim.X > Dl17Scene.EndAt && !sim.Busy) { _ended = true; sim.Checkpoints.Reach("workshop"); sim.Cue(MusicEnd); }
            }
            if (sim.X > Dl17Scene.WorkshopAt) sim.Checkpoints.Reach("workshop");                                  // L5803
        }

        public override bool HasLeft(ChapterSim sim) => _ended;
    }

    /// <summary>The tray off the plan chest (<c>'att:tray'</c>, L5657–L5671): 0.15 short of it facing +1, Lift turned into the set; f22 it comes off at his x, f39 in his hands.</summary>
    public sealed class TrayLiftAct : AttAct
    {
        public static readonly ActId Tray = ActId.Of("dl17.tray"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _tray;
        private bool _off;

        public TrayLiftAct(ChapterSim sim, CarriedItem tray) : base(sim, Tray, Dl17Scene.TrayStand, 1) { _tray = tray; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Lift; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 22 && !_off) { _off = true; _tray.MoveTo(ItemState.Carried, X, _tray.BaseY); }
            if (!(f >= 39)) return true;
            Take(_tray);
            return false;
        }
    }

    /// <summary>The drawer pulled (<c>'att:drawer'</c>, L5662, L5695–L5699): at the drawer facing +1, Tug turned into the set; at 0.35 s it slides; at 1.6 s he is done.</summary>
    public sealed class DrawerAct : AttAct
    {
        public static readonly ActId Drawer = ActId.Of("dl17.drawer"), Tug = ActId.Of("Tug");
        private readonly Dl17Drawer _drawer;
        private bool _pulled;

        public DrawerAct(ChapterSim sim, Dl17Drawer drawer) : base(sim, Drawer, Dl17Scene.DrawerX, 1) { _drawer = drawer; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Tug; }

        protected override bool OnClip(double dt)
        {
            if (T > 0.35 && !_pulled) { _pulled = true; _drawer.Pull(); }
            return !(T > 1.6);
        }
    }

    /// <summary>
    /// Her drawing and her placement read (<c>'att:read'</c>, L5663, L5700–L5707): 0.65 aside of the drawer facing +1,
    /// ReadRoute turned into the set, for 6 s; then it is read (the records scan themselves) and the T-key is his.
    /// </summary>
    public sealed class ReadAct : AttAct
    {
        public static readonly ActId Reading = ActId.Of("dl17.read"), ReadRoute = ActId.Of("ReadRoute");
        public const double ReadFor = 6.0;
        private readonly Dl17Rules _rules;

        public ReadAct(ChapterSim sim, Dl17Rules rules) : base(sim, Reading, Dl17Scene.ReadStand, 1) { _rules = rules; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = ReadRoute; }

        protected override bool OnClip(double dt)
        {
            if (!(T > ReadFor) || _rules.Read) return true;
            _rules.OnRead(Sim);
            return false;
        }
    }
}
