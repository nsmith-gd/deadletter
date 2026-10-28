using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl14a
{
    /// <summary>
    /// DL-14a Lights Out (port_architecture §5; docs/chapter1_expansion_build.md, the redesign in
    /// docs/research/puzzle_design_2d.md): out of the duct onto bunk 1. The door opens once the room has been dark for
    /// 1.2 s: the night-light's sun down (brake it in its dark), and both blinds down, W1 and W2, which one crank swaps.
    /// W1's cord comes down to a hook by the crank: the child's light gown on it rides up with W1, the laundry bag from the
    /// basket holds it down, and the next wind sends W2 down alone. Region 6 from 248 to DL-14b at 263 (<c>sceneName</c>,
    /// L8136). Lines are index.html at 7b3c123 (<c>ATT3</c> L5885–L5896, <c>resetAtt3</c> L5912–L5916,
    /// <c>nearAtt3Item</c>/<c>Fixed</c> L5974–L5991, <c>beginAtt3</c>/<c>updateAtt3Act</c> L6004–L6105, <c>updateAtt3</c>
    /// L6217–L6228, L6255).
    /// </summary>
    public static class Dl14aScene
    {
        public const string Id = "DL-14a";

        public const double X0 = 248, X1 = 263;

        /// <summary><c>ATT3.hookX</c>, <c>bagX</c>, <c>wallPeg.x</c> (L5891–L5893): W1's cord hook by the crank, the laundry basket, the wall peg.</summary>
        public const double HookX = 259.4, BagX = 260.3, WallPegX = 251.5;
        /// <summary>Where the gown waits (and falls) by the hook: <c>hookX + 0.3</c> (L5914, L6040).</summary>
        public const double GownX = HookX + 0.3;
        /// <summary><c>ATT3_STAND.bagBasket</c> (L6004): 0.3 short of the basket.</summary>
        public const double BasketStand = BagX - 0.3;
        /// <summary>How far he steps back for the hook and the wall peg (<c>STEP_IN14a</c>, three −0.5 and −1.0, L6003).</summary>
        public const double HookStep = 0.5, WallStep = 1.0;
        /// <summary>Within reach of the hook (L5977), the basket (L5978), the peg (L5981); W1 low enough to reach its hook (L5976).</summary>
        public const double HookReach = 0.32, BasketReach = 0.35, PegReach = 0.35, HookLow = 0.95;
        /// <summary>The receivers (<see cref="ItemState.Placed"/> slots): W1's cord hook; the gown's wall peg; the bag's basket.</summary>
        public const int HookSlot = 0, WallPegSlot = 1, BasketSlot = 1;
        /// <summary>The <c>corridor</c> checkpoint (DL-14b's) once through the open door (<c>door.x1 + 0.4</c>, L6255).</summary>
        public const double CorridorAt = Dl14aLane.DoorX1 + 0.4;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "Lights Out",
            X0 = X0, X1 = X1,
            Region = Dl14aLane.Region,                                                            // its checkpoint: dorm (the duct's end)
            // Step order = the prototype's: the gown and the bag move and the brake drops in updatePlayer (#4); then updateAtt3
            // runs the night-light, winds the chain, holds W1 under the bag and opens the door (#7, L6219–L6228).
            Mechanisms = new[]
            {
                new MechanismDef("dl14a.gown", () => new CarriedItem("dl14a.gown", GownParams())),
                new MechanismDef("dl14a.bag", () => new CarriedItem("dl14a.bag", BagParams())),
                new MechanismDef("dl14a.hook", () => new Dl14aHook("dl14a.hook")),
                new MechanismDef("dl14a.brake", () => new CycleBrake("dl14a.brake", CycleBrakeParams.Dl14aBrake())),
                new MechanismDef("dl14a.crank", () => new WindCrank("dl14a.crank", WindCrankParams.Dl14aCrank())),
                new MechanismDef("dl14a.blinds", () => new PairedBlindDrive("dl14a.blinds", PairedBlindParams.Dl14aBlinds())),
                new MechanismDef("dl14a.nightLight", () => new CycleClock("dl14a.nightLight", CycleClockParams.Dl14aNightLight())),
                new MechanismDef("dl14a.door", () => new Door("dl14a.door", DoorParams.Dl14aDoor())),
            },
            Lane = Dl14aLane.Table,
            LaneContributors = Dl14aLane.Contributors,
            Rules = () => new Dl14aRules(),
        };

        /// <summary>
        /// The child's gown (<c>f14a.gown</c>, L5914; <c>itemsAtt3</c> L5937: r 0.16, below 0.02, light): on W1's cord hook,
        /// x the hook's + 0.3; on the floor there once the room has been dark (<c>corridor</c>). Never standable.
        /// </summary>
        public static CarriedItemParams GownParams() => new CarriedItemParams
        {
            HomeX = GownX, HomeBaseY = 0, HomeState = ItemState.Placed, HomeSlot = HookSlot,
            Radius = 0.16, Solid = false, BelowWrist = 0.02, IsLight = true,
            MovedAfter = "corridor", MovedState = ItemState.Floor, MovedX = GownX, MovedBaseY = 0,
        };

        /// <summary>
        /// The laundry bag (<c>f14a.bag</c>, L5915; L5938: r 0.18, below 0.02, heavy): in the basket at the hook's x; on the
        /// hook from <c>corridor</c>. Never standable.
        /// </summary>
        public static CarriedItemParams BagParams() => new CarriedItemParams
        {
            HomeX = HookX, HomeBaseY = 0, HomeState = ItemState.Placed, HomeSlot = BasketSlot,
            Radius = 0.18, Solid = false, BelowWrist = 0.02, IsLight = false,
            MovedAfter = "corridor", MovedState = ItemState.Placed, MovedX = HookX, MovedBaseY = 0, MovedSlot = HookSlot,
        };

        internal static bool IsAt(CarriedItem it, int slot) => it.State == ItemState.Placed && it.Slot == slot;
    }

    /// <summary>
    /// W1's cord hook (<c>dl14a.hook</c>): engaged while the laundry bag hangs on it, its weight holding W1 down
    /// (<c>A.bag.state === 'hook'</c>, L6087, L6223). Stateless; it reads the bag as it is this step.
    /// </summary>
    public sealed class Dl14aHook : Mechanism, IEngageable
    {
        private CarriedItem _bag;

        public Dl14aHook(MechanismId id) : base(id) { }

        public bool Engaged => _bag != null && Dl14aScene.IsAt(_bag, Dl14aScene.HookSlot);

        public override void Link(MechanismLinker link) => _bag = link.Read<CarriedItem>("dl14a.bag")
            ?? throw new InvalidOperationException(Id + " needs dl14a.bag.");

        public override void Reset(in Checkpoint cp) => Init(0);
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }

    /// <summary>
    /// DL-14a's rules: Use with the gown and the bag (<c>nearAtt3Item</c>, L5974–L5983, asked before anything else in
    /// region 6): the bag out of its basket, something onto W1's hook (or a reach for it while W1 is up), something off the
    /// hook, the gown onto the wall peg (a wrong first try) and back; the door's opening and the <c>corridor</c> checkpoint
    /// past it (L6225, L6255). <see cref="Always"/>: <c>corridor</c> is reached in DL-14b's stretch.
    /// </summary>
    public sealed class Dl14aRules : SceneRules
    {
        public static readonly CueId SoundDoor = CueId.Of("sound:door");
        private static readonly MechanismId DoorId = "dl14a.door";

        private CarriedItem _gown, _bag;
        private PairedBlindDrive _blinds;
        private Door _door;

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _gown = g.Get<CarriedItem>("dl14a.gown"); _bag = g.Get<CarriedItem>("dl14a.bag");
            _blinds = g.Get<PairedBlindDrive>("dl14a.blinds"); _door = g.Get<Door>(DoorId);
        }

        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded || sim.Region != Dl14aLane.Region) return;
            double x = m.X, y = m.Y;
            var carry = m.Hold == HoldKind.Item ? m.Carried : null;
            bool free = m.Hold == HoldKind.None, low = _blinds.A > Dl14aScene.HookLow, atHook = y < 0.05 && Math.Abs(x - Dl14aScene.HookX) < Dl14aScene.HookReach;
            SceneAct act = null;
            if (free && Dl14aScene.IsAt(_bag, Dl14aScene.BasketSlot) && y < 0.05 && Math.Abs(x - Dl14aScene.BagX) < Dl14aScene.BasketReach)
                act = new BagOutAct(sim, _bag);                                                                                     // L5978
            else if (atHook && carry != null && (carry == _gown || carry == _bag))
                act = low ? (SceneAct)new HangOnHookAct(sim, _gown, _bag) : new ReachHookAct(sim);                                 // L5979
            else if (atHook && free && low && (Dl14aScene.IsAt(_gown, Dl14aScene.HookSlot) || Dl14aScene.IsAt(_bag, Dl14aScene.HookSlot)))
                act = new TakeOffHookAct(sim, Dl14aScene.IsAt(_bag, Dl14aScene.HookSlot) ? _bag : _gown, _blinds);              // L5980
            else if (carry == _gown && y < 0.05 && Math.Abs(x - Dl14aScene.WallPegX) < Dl14aScene.PegReach)
                act = new GownOnWallAct(sim, _gown);                                                                                // L5981
            else if (free && Dl14aScene.IsAt(_gown, Dl14aScene.WallPegSlot) && y < 0.05 && Math.Abs(x - Dl14aScene.WallPegX) < Dl14aScene.PegReach)
                act = new GownOffWallAct(sim, _gown);                                                                               // L5982
            if (act == null) return;
            input = MotorInput.None;
            sim.StartAct(act);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Graph.Log.Has(DoorId, MechanismEventKind.State, (int)DoorState.Opening)) sim.Cue(SoundDoor);       // L6225
            if (sim.Region == Dl14aLane.Region && sim.X > Dl14aScene.CorridorAt && _door.State != DoorState.Closed) sim.Checkpoints.Reach("corridor");   // L6255
        }
    }

    /// <summary>The bag out of its basket (<c>'att:bagBasket'</c>, L6025, L6096–L6102): 0.3 short of the basket, Lift turned into the set; f22 it is out at his x, f39 in his hands.</summary>
    public sealed class BagOutAct : AttAct
    {
        public static readonly ActId Basket = ActId.Of("dl14a.basket"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _bag;
        private bool _out;

        public BagOutAct(ChapterSim sim, CarriedItem bag) : base(sim, Basket, Dl14aScene.BasketStand, 1) { _bag = bag; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Lift; }

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 22 && !_out) { _out = true; _bag.MoveTo(ItemState.Carried, X, _bag.BaseY); }
            if (!(f >= 39)) return true;
            Take(_bag);
            return false;
        }
    }

    /// <summary>
    /// What he carries onto W1's cord hook (<c>'att:hangHook'</c>, L6036–L6046): to the hook, a step back toward it, SetDownHigh;
    /// f14 it hangs there (and whatever hung there falls to the floor by it), his hands empty; f35 he steps out again.
    /// </summary>
    public sealed class HangOnHookAct : AttAct
    {
        public static readonly ActId Hook = ActId.Of("dl14a.hook"), SetDownHigh = ActIds.Clip(ClipNames.SetDownHigh);
        private readonly CarriedItem _gown, _bag;
        private bool _hung;

        public HangOnHookAct(ChapterSim sim, CarriedItem gown, CarriedItem bag) : base(sim, Hook, Dl14aScene.HookX, 1, Dl14aScene.HookStep) { _gown = gown; _bag = bag; }

        protected override void OnArrive() => Phase = SetDownHigh;

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 14 && !_hung && Held is CarriedItem it && it.State == ItemState.Carried)
            {
                _hung = true;
                var other = it == _bag ? _gown : _bag;
                if (Dl14aScene.IsAt(other, Dl14aScene.HookSlot)) other.MoveTo(ItemState.Floor, Dl14aScene.GownX, 0);   // L6040
                it.MoveTo(ItemState.Placed, it.X, it.BaseY, Dl14aScene.HookSlot);
                LetGo();
            }
            return !(f >= 35);
        }
    }

    /// <summary>
    /// What hangs on W1's hook, back off it (<c>'att:takeHook'</c>, L6047–L6051): the bag if it is there, else the gown; a step
    /// back, Lift; f22 it comes off at his x, its base half a metre under the hook; f39 it is in his hands; he steps out.
    /// </summary>
    public sealed class TakeOffHookAct : AttAct
    {
        public static readonly ActId Hook = ActId.Of("dl14a.hook"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _it;
        private readonly PairedBlindDrive _blinds;
        private bool _off, _held;

        public TakeOffHookAct(ChapterSim sim, CarriedItem it, PairedBlindDrive blinds) : base(sim, Hook, Dl14aScene.HookX, 1, Dl14aScene.HookStep) { _it = it; _blinds = blinds; }

        protected override void OnArrive() => Phase = Lift;

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 22 && !_off) { _off = true; _it.MoveTo(ItemState.Carried, X, _blinds.HookY - 0.5); }   // hook14a(A.w1) − 0.5
            if (f >= 39 && !_held) { _held = true; Take(_it); return false; }
            return true;
        }
    }

    /// <summary>The gown onto the wall peg (<c>'att:hangWall'</c>, L6053–L6056: a wrong first try): a long step back, SetDownHigh; f14 it hangs; f35 he steps out.</summary>
    public sealed class GownOnWallAct : AttAct
    {
        public static readonly ActId Peg = ActId.Of("dl14a.wallPeg"), SetDownHigh = ActIds.Clip(ClipNames.SetDownHigh);
        private readonly CarriedItem _gown;
        private bool _hung;

        public GownOnWallAct(ChapterSim sim, CarriedItem gown) : base(sim, Peg, Dl14aScene.WallPegX, 1, Dl14aScene.WallStep) { _gown = gown; }

        protected override void OnArrive() => Phase = SetDownHigh;

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 14 && !_hung && Held == _gown)
            {
                _hung = true;
                _gown.MoveTo(ItemState.Placed, _gown.X, _gown.BaseY, Dl14aScene.WallPegSlot);
                LetGo();
            }
            return !(f >= 35);
        }
    }

    /// <summary>The gown back off the wall peg (<c>'att:takeWall'</c>, L6057–L6061): a long step back, Lift; f22 it comes off at his x; f39 in his hands; he steps out.</summary>
    public sealed class GownOffWallAct : AttAct
    {
        public static readonly ActId Peg = ActId.Of("dl14a.wallPeg"), Lift = ActIds.Clip(ClipNames.Lift);
        private readonly CarriedItem _gown;
        private bool _off, _held;

        public GownOffWallAct(ChapterSim sim, CarriedItem gown) : base(sim, Peg, Dl14aScene.WallPegX, 1, Dl14aScene.WallStep) { _gown = gown; }

        protected override void OnArrive() => Phase = Lift;

        protected override bool OnClip(double dt)
        {
            double f = Frame;
            if (f >= 22 && !_off) { _off = true; _gown.MoveTo(ItemState.Carried, X, _gown.BaseY); }
            if (f >= 39 && !_held) { _held = true; Take(_gown); return false; }
            return true;
        }
    }

    /// <summary>
    /// Carrying something to the hook while W1 is up (<c>'att:reachHook'</c>, L6063–L6068): no approach; he stretches for it
    /// (Present) and looks at the crank that winds it, until 2.4 s, still carrying it.
    /// </summary>
    public sealed class ReachHookAct : AttAct
    {
        public static readonly ActId Reach = ActId.Of("dl14a.reachHook"), Present = ActIds.Clip(ClipNames.Present);

        public ReachHookAct(ChapterSim sim) : base(sim, Reach, double.NaN, 0) { Phase = Present; }

        protected override void OnArrive() { }

        protected override bool OnClip(double dt) => !(T > 2.4);
    }
}
