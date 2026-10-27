using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl03
{
    public enum Dl03WeightState
    {
        /// <summary>On the floor (<c>'floor'</c>).</summary>
        Floor,
        /// <summary>In his claws (<c>'carried'</c>, from Lift f22).</summary>
        Carried,
        /// <summary>On the trolley's deck, <see cref="Dl03Weight.Offset"/> from its centre (<c>'trolley'</c>).</summary>
        OnTrolley,
    }

    public sealed class Dl03WeightParams
    {
        /// <summary><c>WEIGHT_X</c> = OFF2 + 12.62, L320.</summary>
        public double StartX = 13 + 12.62;
        /// <summary>Solved: on the trolley, 0.12 left of its centre (<c>{ x: OFF2 + 16.0, state: 'trolley', off: −0.12 }</c>, L8025).</summary>
        public string OnTrolleyAfter = "solved";
        public double ParkedX = 13 + 16.0, ParkedOffset = -0.12;
        /// <summary>The trolley it rides (an <see cref="IPositionSource"/>: its x).</summary>
        public MechanismId Trolley = "dl03.trolley";
        /// <summary><c>WEIGHT_R</c>, <c>WEIGHT_H</c>, <c>BAIL_BELOW_WRIST</c>, <c>GRIP_FWD</c> (L320); <c>TROLLEY_DECK</c> (L321).</summary>
        public double Radius = 0.1, Height = 0.22, BelowWrist = 0.28, GripForward = 0.29, Deck = 0.16;
    }

    /// <summary>
    /// DL-03's sorting weight: the minimal scene-local carryable (U-11's <see cref="ICarryable"/>) and a body the plate
    /// weighs (<see cref="IPlateBody"/>). He lifts it from the floor (the motor's Lift: approach to GRIP_FWD short of it,
    /// L1826; f22 it is his, L2278) and sets it down in front of him, on the trolley's deck if it is there, else on clear
    /// floor (<see cref="Dl03SetDownAct"/>, L2261–L2271, L2280–L2287). Callbacks record; <see cref="Step"/> applies.
    /// <para><b>Moves to Core/Carry at merge</b> (DL-02 owns Core/Carry): it is a <c>CarriedItem</c> with a carrier
    /// state; only <see cref="CanStandAt"/>'s wiring and the deck offset are DL-03's.</para>
    /// </summary>
    public sealed class Dl03Weight : Mechanism, ICarryable, IPlateBody
    {
        private readonly Dl03WeightParams _p;
        private IPositionSource _trolley;
        private bool _lift, _toFloor, _toTrolley;
        private double _pendingX, _pendingOff;
        private double _x;

        public Dl03Weight(MechanismId id, Dl03WeightParams p = null) : base(id) { _p = p ?? new Dl03WeightParams(); }

        public Dl03WeightParams Params => _p;
        public Dl03WeightState State => (Dl03WeightState)StateCode;
        /// <summary>Its offset from the trolley's centre while on it (<c>w.off</c>).</summary>
        public double Offset { get; private set; }
        /// <summary>The prototype's <c>w.x</c>: where it was last on the floor (kept while carried or on the trolley).</summary>
        public double FloorX => _x;

        /// <summary>Can he stand at a stand point (DL-03's <c>standFree</c>, L2239–L2242)? Wired by the scene; null = anywhere.</summary>
        public Func<double, bool> CanStandAt { get; set; }

        // ---- ICarryable ---------------------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Item;
        /// <summary>Lane x of its centre (<c>weightX()</c>, L2228).</summary>
        public double X => State == Dl03WeightState.OnTrolley ? _trolley.Position + Offset : _x;
        public double BaseY => State == Dl03WeightState.OnTrolley ? _p.Deck : 0;
        public double Radius => _p.Radius;
        public double BelowWrist => _p.BelowWrist;
        public bool IsLight => false;

        /// <summary>
        /// <c>nearUse2</c>'s lift (L2251–L2254): only from the floor, and only if he can stand GRIP_FWD short of it on his
        /// side. The resolver adds reach (|x − stand| &lt; 0.4) and level (y within 0.05).
        /// </summary>
        public bool IsAvailable(in InteractionQuery q)
        {
            if (State != Dl03WeightState.Floor) return false;
            if (CanStandAt == null) return true;
            int side = Smooth.Sign(_x - q.X);
            if (side == 0) side = q.Facing;
            return CanStandAt(_x - side * _p.GripForward);
        }

        /// <summary>Lift f22: it is his (<c>w.state = 'carried'</c>, L2278).</summary>
        public void OnLifted() => _lift = true;

        /// <summary>Set down on the floor at <paramref name="x"/> (<c>w.state = 'floor'; w.x = a.tx</c>, L2284).</summary>
        public void OnSetDown(double x, double baseY) { _toFloor = true; _pendingX = x; }

        /// <summary>Set down on the trolley's deck, <paramref name="offset"/> from its centre (<c>w.off = a.tx − t.x</c>, L2284).</summary>
        public void OnSetDownOnTrolley(double offset) { _toTrolley = true; _pendingOff = offset; }

        // ---- IPlateBody ---------------------------------------------------------------------------------------------
        double IPlateBody.X => X;
        public double SupportX => State == Dl03WeightState.OnTrolley ? _trolley.Position : _x;
        public BodySupport Support => State == Dl03WeightState.Carried ? BodySupport.Carried
            : State == Dl03WeightState.OnTrolley ? BodySupport.Carrier : BodySupport.Floor;

        // ---- Mechanism ----------------------------------------------------------------------------------------------
        public override void Link(MechanismLinker link)
            => _trolley = link.Read<IPositionSource>(_p.Trolley) ?? throw new InvalidOperationException(Id + " needs its trolley.");

        public override void Reset(in Checkpoint cp)
        {
            bool solved = cp.Past(_p.OnTrolleyAfter);
            _x = solved ? _p.ParkedX : _p.StartX;
            Offset = solved ? _p.ParkedOffset : 0;
            _lift = _toFloor = _toTrolley = false;
            _pendingX = _pendingOff = 0;
            Init((int)(solved ? Dl03WeightState.OnTrolley : Dl03WeightState.Floor));
        }

        public override void Step(in StepContext ctx)
        {
            if (_lift && State == Dl03WeightState.Floor) Enter(ctx, (int)Dl03WeightState.Carried);
            if (_toTrolley && State == Dl03WeightState.Carried) { Offset = _pendingOff; Enter(ctx, (int)Dl03WeightState.OnTrolley); }
            else if (_toFloor && State == Dl03WeightState.Carried) { _x = _pendingX; Enter(ctx, (int)Dl03WeightState.Floor); }
            _lift = _toFloor = _toTrolley = false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", _x); w.WriteDouble("off", Offset);
            w.WriteBool("lift", _lift); w.WriteBool("toFloor", _toFloor); w.WriteBool("toTrolley", _toTrolley);
            w.WriteDouble("px", _pendingX); w.WriteDouble("poff", _pendingOff);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _x = r.ReadDouble("x"); Offset = r.ReadDouble("off");
            _lift = r.ReadBool("lift"); _toFloor = r.ReadBool("toFloor"); _toTrolley = r.ReadBool("toTrolley");
            _pendingX = r.ReadDouble("px"); _pendingOff = r.ReadDouble("poff");
        }
    }
}
