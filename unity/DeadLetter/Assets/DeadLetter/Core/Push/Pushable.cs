using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Push
{
    public enum PushableState
    {
        /// <summary>On the floor, his to grab or held (<c>state 'free'</c>; while held <see cref="Pushable.Held"/>).</summary>
        Free,
        /// <summary>Held at a pit's lip with its front wheels over, teetering (<c>s.lip</c>, L4730).</summary>
        AtLip,
        /// <summary>Tipping into the pit (<see cref="TipIntoPit"/>).</summary>
        Falling,
        /// <summary>In the pit: a bridge (<c>'bridge'</c>).</summary>
        Settled,
        /// <summary>At the end of its travel and set there: the courier in its cradle, the drum set, the body on the plate (L4723–L4735).</summary>
        Docked,
    }

    public enum PushableEvent
    {
        /// <summary>It goes over the lip (<c>tipOver</c>, L4739).</summary>
        Tip,
        /// <summary>It lands in the pit; Value = shake (L4757, L4855).</summary>
        Land,
        /// <summary>It docked at the end of its travel (<c>'cradle'</c>, <c>'set'</c>, <c>'plate'</c>, L4729–L4734).</summary>
        Dock,
    }

    /// <summary>A body it stops against while that body stands on the floor, <see cref="Gap"/> short of its centre either way.</summary>
    public readonly struct PushBlock
    {
        public readonly MechanismId Body;
        public readonly double Gap;

        public PushBlock(MechanismId body, double gap) { Body = body; Gap = gap; }
    }

    /// <summary>
    /// A pushable's data (port_architecture §4.11 table; <c>PUSHABLES</c> L4273–L4295, the old holds L2318–L2361). The
    /// face he grabs it by is <see cref="Side"/>; a <see cref="PushTwin"/> is the other face. Values resolved and cited.
    /// </summary>
    public sealed class PushableParams
    {
        /// <summary>Where it stands in a new game.</summary>
        public double StartX;
        /// <summary>From this checkpoint on (<see cref="Checkpoint.Past"/>) it is at <see cref="ParkedX"/> in <see cref="ParkedState"/>.</summary>
        public string ParkedAfter;
        public double ParkedX;
        public PushableState ParkedState = PushableState.Free;
        /// <summary>+1: he stands left of it and pushes right; −1 the other way.</summary>
        public int Side = +1;
        /// <summary>His centre is X − Side·Gap while he holds it.</summary>
        public double Gap;
        /// <summary>Top speed held, m/s; <see cref="LoadedSpeed"/> while a <see cref="Riders"/> body rides it (NaN = the same).</summary>
        public double Speed, LoadedSpeed = double.NaN;
        /// <summary>Bodies (<see cref="IPlateBody"/>) that can ride on it: loaded while one's support is <see cref="BodySupport.Carrier"/>.</summary>
        public MechanismId[] Riders = Array.Empty<MechanismId>();
        /// <summary>
        /// The prototype's hold acceleration, m/s² (old holds 3, the heavy ones 1.3, L2332; chapter 1 1.4, L4690). U-11 gap
        /// (#22): <see cref="IPushable"/> has no acceleration, so the motor uses <see cref="Motor.MotorConfig.AccelPush"/> for
        /// every pushable; a scene sets that to this value (<c>SceneDef.Motor</c>).
        /// </summary>
        public double Accel = 1.4;
        /// <summary>Its travel (for a pit, <see cref="Max"/> is the lip, <see cref="TipParams.LipX"/>).</summary>
        public double Min, Max;
        /// <summary>Bodies it stops against while they stand on the floor (DL-03's weight, L2343–L2346).</summary>
        public PushBlock[] Blocks = Array.Empty<PushBlock>();
        /// <summary>Ascending stops (<see cref="Push.Detents"/>); empty = none.</summary>
        public double[] Detents = Array.Empty<double>();
        /// <summary>
        /// A first stop short of <see cref="Max"/> (NaN = none): while it stands more than <see cref="Pushable.StopSlack"/>
        /// short of it, its travel ends there; past that, at Max. Unlike a detent it is read from where it stands, not
        /// where he took hold, and he keeps hold (DL-05's drum: <c>x &lt; drumPlate − 0.01 ? drumPlate : drumPark</c>, L4277).
        /// </summary>
        public double StopAt = double.NaN;
        /// <summary>
        /// Grabbable only while it can still move more than this toward its travel's end (NaN = always): DL-05's body,
        /// <c>avail: max() − x &gt; 0.05</c> (L4281).
        /// </summary>
        public double MinRoom = double.NaN;
        /// <summary>The pit it tips into at <see cref="Max"/>; null = none.</summary>
        public TipParams Pit;
        /// <summary>Reaching the end of its travel within <see cref="DockTolerance"/> of this docks it (NaN = never).</summary>
        public double DockAt = double.NaN, DockTolerance = 0.01;
        /// <summary>Floor level he grabs it from, and the depth he steps to while approaching (Unity z, L4461).</summary>
        public double FloorY, Z;
        /// <summary>Grip reach with him in front of / behind the stand point (L4254, L4274; DL-03 0.34 both ways, L2257).</summary>
        public double ForwardReach = 0.34, BackReach = 0.34;
        /// <summary>The body on the lane: half-length and the height of its top (a lane contributor makes it standable).</summary>
        public double Half, Top;

        /// <summary>
        /// DL-03: the trolley, grabbed at either end (<see cref="PushTwin"/> for the right one, <c>grabR</c>), 0.62 from its
        /// centre; 0.55 m/s, 0.42 with the weight on it, accel 3; from 25.44 to 29.97, stopping 0.39 short of the weight on
        /// the floor; parked on the plate once solved (L321–L325, L2255–L2258, L2329–L2348, L8026).
        /// </summary>
        public static PushableParams Dl03Trolley() => new PushableParams
        {
            StartX = 13 + 14.55,                                                  // TROLLEY_X = OFF2 + 14.55, L321
            ParkedAfter = "solved", ParkedX = (13 + 15.8 + (13 + 16.55)) / 2,    // (PLATE.x0 + PLATE.x1) / 2, L8026
            Side = +1, Gap = 0.62,                                                // grabL, PUSH_GAP L321
            Speed = 0.55, LoadedSpeed = 0.42, Riders = new MechanismId[] { "dl03.weight" },   // PUSH_SPEED, PUSH_LOADED L325; L2330
            Accel = 3,                                                            // L2332
            Min = 13 + 12.1 + 0.06 + 0.28, Max = 13 + 17.6 - 0.35 - 0.28,         // TROLLEY_MIN/MAX L322 (ROOM_X0, TROLLEY_HALF)
            Blocks = new[] { new PushBlock("dl03.weight", 0.28 + 0.1 + 0.01) },  // TROLLEY_HALF + WEIGHT_R + 0.01, L2344
            FloorY = 0, Z = 0, ForwardReach = 0.34, BackReach = 0.34,             // y ≤ 0.05; |x − stand| < 0.34, L2249, L2257
            Half = 0.28, Top = 0.16,                                              // TROLLEY_HALF, TROLLEY_DECK L321; surfaceAt L1725
        };
    }

    /// <summary>
    /// A push/pull/drag object (port_architecture §4.11; Core/Push): U-11's <see cref="IPushable"/> by its
    /// <see cref="PushableParams.Side"/> face (<see cref="PushTwin"/> is the other), and a mechanism the plates weigh
    /// (<see cref="IPlateBody"/>). The motor moves it while he holds it (<see cref="MoveTo"/>); the callbacks only record,
    /// <see cref="Step"/> applies (tipping, docking). Its travel is [Min, Max] narrowed by bodies standing in the way
    /// (<see cref="PushableParams.Blocks"/>) and by <see cref="Detents"/>; with a <see cref="PushableParams.Pit"/> it tips
    /// in from the lip (<see cref="TipIntoPit"/>). DL-03's trolley; the pattern for DL-04's courier, DL-05's drum and
    /// body, DL-08's goods trolley, DL-12/13's figures, DL-15's figures and DL-16a's stool.
    /// <para>Signals: <see cref="Position"/> = x, metres; <see cref="Engaged"/> = docked or settled in its pit.</para>
    /// </summary>
    public sealed class Pushable : Mechanism, IPushable, IPlateBody, IPositionSource, IEngageable
    {
        /// <summary><see cref="PushableParams.StopAt"/> holds while it stands more than this short of it (L4277).</summary>
        public const double StopSlack = 0.01;

        private readonly PushableParams _p;
        private readonly TipIntoPit _tip;
        private IPlateBody[] _riders = Array.Empty<IPlateBody>(), _blocks = Array.Empty<IPlateBody>();
        private bool _held, _moved, _lip, _tipNow, _dockNow;
        private double _from;

        public Pushable(MechanismId id, PushableParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (p.Side != 1 && p.Side != -1) throw new ArgumentException(id + ": Side is +1 or −1.");
            if (!(p.Max >= p.Min)) throw new ArgumentException(id + ": Max < Min.");
            if (p.Detents.Length > 0 && !Push.Detents.IsAscending(p.Detents)) throw new ArgumentException(id + ": detents must ascend.");
            if (p.Pit != null && p.Detents.Length > 0) throw new ArgumentException(id + ": a pushable tips into a pit or has detents, not both.");
            _tip = p.Pit != null ? new TipIntoPit(p.Pit) : null;
        }

        public PushableParams Params => _p;
        public PushableState State => (PushableState)StateCode;
        /// <summary>Velocity, m/s, while he moves it (<c>t.v</c>, L2348); 0 once he lets go (L2369).</summary>
        public double Velocity { get; private set; }
        /// <summary>He has it in his hands: from the first step the motor moves it until he lets go.</summary>
        public bool Held => _held;
        /// <summary>A rider is on it (<c>w.state === 'trolley'</c>, L2330).</summary>
        public bool Loaded
        {
            get
            {
                for (int i = 0; i < _riders.Length; i++) if (_riders[i].Support == BodySupport.Carrier) return true;
                return false;
            }
        }
        /// <summary>The fall into its pit (null without one).</summary>
        public TipIntoPit Tip => _tip;

        /// <summary>
        /// Can he stand at a stand point (lane x)? The scene wires it to its lane (DL-03's <c>standFree</c>, L2239–L2242);
        /// null: anywhere. Called from the resolver, so it reads state only.
        /// </summary>
        public Func<double, bool> CanStandAt { get; set; }

        // ---- Signals ------------------------------------------------------------------------------------------------
        public double Position => X;
        public bool Engaged => State == PushableState.Docked || State == PushableState.Settled;
        public double SupportX => X;
        public BodySupport Support
            => State == PushableState.Falling || State == PushableState.Settled ? BodySupport.Away : _held ? BodySupport.Pushed : BodySupport.Floor;

        // ---- IPushable (the Side face) ------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Push;
        /// <summary>Lane x of its centre.</summary>
        public double X { get; private set; }
        public int Side => _p.Side;
        public double Gap => _p.Gap;
        public double Speed => !double.IsNaN(_p.LoadedSpeed) && Loaded ? _p.LoadedSpeed : _p.Speed;
        public double Min { get { Range(out double lo, out _); return lo; } }
        public double Max { get { Range(out _, out double hi); return hi; } }
        public double FloorY => _p.FloorY;
        public double Z => _p.Z;
        public double ForwardReach => _p.ForwardReach;
        public double BackReach => _p.BackReach;
        public bool TipsIntoPit => _tip != null;
        public bool HasDetents => _p.Detents.Length > 0;

        public bool IsAvailable(in InteractionQuery q) => IsAvailableFrom(_p.Side, q);

        /// <summary>Grabbable from the face <paramref name="side"/>: on the floor, and he can stand at its stand point.</summary>
        public bool IsAvailableFrom(int side, in InteractionQuery q)
            => (State == PushableState.Free || State == PushableState.AtLip) && (CanStandAt == null || CanStandAt(X - side * _p.Gap))
               && (double.IsNaN(_p.MinRoom) || Max - X > _p.MinRoom);

        /// <summary>
        /// Its travel now: [Min, Max] narrowed by its <see cref="PushableParams.StopAt"/> while short of it, the
        /// <see cref="PushableParams.Blocks"/> standing on the floor (L2343–L2346: stops gap short of a body ahead or behind)
        /// and the <see cref="Detents"/> either side of where he took hold.
        /// </summary>
        public void Range(out double lo, out double hi)
        {
            lo = _p.Min; hi = _p.Max;
            if (!double.IsNaN(_p.StopAt) && X < _p.StopAt - StopSlack && hi > _p.StopAt) hi = _p.StopAt;   // L4277
            for (int i = 0; i < _blocks.Length; i++)
            {
                var b = _blocks[i];
                if (b.Support != BodySupport.Floor) continue;
                double gap = _p.Blocks[i].Gap;
                if (b.X > X && hi > b.X - gap) hi = b.X - gap;
                if (b.X < X && lo < b.X + gap) lo = b.X + gap;
            }
            if (_p.Detents.Length > 0) Push.Detents.Clamp(_p.Detents, _held ? _from : X, ref lo, ref hi);
        }

        /// <summary>The motor moves it while held (<c>t.x = tx; t.v = …</c>, L2347–L2348, L4697).</summary>
        public void MoveTo(double x, double velocity)
        {
            if (!_held) { _held = true; _from = X; }                  // game.pushFrom: where he took hold
            X = x; Velocity = velocity; _moved = true;
        }

        public void SetAtLip(bool atLip) => _lip = atLip;

        /// <summary>He let go (Jump or Use). At the lip it tips in (L4688).</summary>
        public void OnReleased(bool atLip)
        {
            _held = false;
            if (atLip && _tip != null) _tipNow = true; else _lip = false;
        }

        /// <summary>Held into the lip for 0.45 s: a last shove (L4708–L4715).</summary>
        public void OnShoved() { _held = false; if (_tip != null) _tipNow = true; }

        /// <summary>The motor reached Max (not tipping, no detents) and let go: it docks there if that is <see cref="PushableParams.DockAt"/> (L4723–L4735).</summary>
        public void OnTravelEnd()
        {
            _held = false;
            if (!double.IsNaN(_p.DockAt) && Math.Abs(X - _p.DockAt) < _p.DockTolerance) _dockNow = true;
        }

        public override void Link(MechanismLinker link)
        {
            _riders = new IPlateBody[_p.Riders.Length];
            for (int i = 0; i < _riders.Length; i++)
                _riders[i] = link.ReadAnyOrder<IPlateBody>(_p.Riders[i]) ?? throw new InvalidOperationException(Id + ": a rider needs a body.");
            _blocks = new IPlateBody[_p.Blocks.Length];
            for (int i = 0; i < _blocks.Length; i++)
                _blocks[i] = link.ReadAnyOrder<IPlateBody>(_p.Blocks[i].Body) ?? throw new InvalidOperationException(Id + ": a block needs a body.");
        }

        /// <summary>Where the checkpoint puts it (<c>resetWorld</c>: TROLLEY_X, or parked on the plate, L8026).</summary>
        public override void Reset(in Checkpoint cp)
        {
            bool parked = cp.Past(_p.ParkedAfter);
            var s = parked ? _p.ParkedState : PushableState.Free;
            X = parked ? _p.ParkedX : _p.StartX;
            if (s == PushableState.Falling) s = PushableState.Settled;
            if (s == PushableState.Settled)
            {
                if (_tip == null) throw new InvalidOperationException(Id + " has no pit to be settled in.");
                _tip.Settle();
                X = _tip.X;
            }
            Velocity = 0;
            _held = _moved = _lip = _tipNow = _dockNow = false;
            _from = X;
            Init((int)s);
        }

        public override void Step(in StepContext ctx)
        {
            var s = State;
            bool onFloor = s == PushableState.Free || s == PushableState.AtLip;
            if (_tipNow && onFloor)                                                                         // tipOver, L4739
            {
                Enter(ctx, (int)PushableState.Falling);
                _tip.Begin(X);
                _lip = false; _held = false; Velocity = 0;
                Emit(ctx, (int)PushableEvent.Tip);
                onFloor = false;
            }
            _tipNow = false;
            if (_dockNow && onFloor)
            {
                Enter(ctx, (int)PushableState.Docked);
                Emit(ctx, (int)PushableEvent.Dock, 0, X);
                onFloor = false;
            }
            _dockNow = false;
            if (onFloor) Enter(ctx, (int)(_lip ? PushableState.AtLip : PushableState.Free));

            if (State == PushableState.Falling)
            {
                bool settled = _tip.Advance(ctx.Dt, out bool landed);
                X = _tip.X;
                if (landed) Emit(ctx, (int)PushableEvent.Land, 0, _p.Pit.LandShake);
                if (settled) Enter(ctx, (int)PushableState.Settled);
            }

            if (!_moved) Velocity = 0;                                                                      // L2369
            _moved = false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("v", Velocity); w.WriteDouble("from", _from);
            w.WriteBool("held", _held); w.WriteBool("moved", _moved); w.WriteBool("lip", _lip);
            w.WriteBool("tip", _tipNow); w.WriteBool("dock", _dockNow);
            if (_tip == null) return;
            w.WriteDouble("drop", _tip.Drop); w.WriteDouble("tx", _tip.X); w.WriteDouble("t0", _tip.FromX);
            w.WriteDouble("viewY", _tip.ViewY); w.WriteDouble("dip", _tip.DipRad); w.WriteBool("landed", _tip.Landed);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); Velocity = r.ReadDouble("v"); _from = r.ReadDouble("from");
            _held = r.ReadBool("held"); _moved = r.ReadBool("moved"); _lip = r.ReadBool("lip");
            _tipNow = r.ReadBool("tip"); _dockNow = r.ReadBool("dock");
            if (_tip == null) return;
            _tip.Set(r.ReadDouble("drop"), r.ReadDouble("tx"), r.ReadDouble("t0"), r.ReadDouble("viewY"), r.ReadDouble("dip"), r.ReadBool("landed"));
        }
    }
}
