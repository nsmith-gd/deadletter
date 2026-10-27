using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Carry
{
    /// <summary>Where a liftable item is (port_architecture §4.10: the prototype's item <c>state</c> strings).</summary>
    public enum ItemState
    {
        /// <summary>Resting on the lane at (<see cref="CarriedItem.X"/>, <see cref="CarriedItem.BaseY"/>) (<c>'floor'</c>).</summary>
        Floor,
        /// <summary>In his hands, from Lift f22 (<c>'carried'</c>, L4419).</summary>
        Carried,
        /// <summary>Set into a receiver's slot (<see cref="CarriedItem.Slot"/>): a tray, a peg, a lift car (<c>'tray'</c>, <c>'car'</c>).</summary>
        Placed,
        /// <summary>Riding a carrier (<c>'carrier'</c>, DL-06).</summary>
        InCarrier,
        /// <summary>Out of the lane (<c>'gone'</c>, <c>'bucket'</c>).</summary>
        Gone,
        /// <summary>Tumbling off a carrier (<c>'tumble'</c>, DL-06, L4957).</summary>
        Tumble,
    }

    public enum ItemEvent
    {
        /// <summary>Lift f22: it leaves its rest (<c>Sound.scrape</c>, L4419).</summary>
        Lifted,
        /// <summary>SetDown f14: on the lane at Value = x (<c>Sound.setDown</c>, L4425). The view drops it over <see cref="CarriedItem.DropSeconds"/>.</summary>
        SetDown,
        /// <summary>Moved by its receiver (placed, loaded, gone, tumbling): Index = the new <see cref="ItemState"/>.</summary>
        Moved,
    }

    public sealed class CarriedItemParams
    {
        /// <summary>Where it rests at the start: lane x and the height it stands on.</summary>
        public double HomeX, HomeBaseY;
        /// <summary>Half-width for the set-down flatness test (<c>it.r</c>, L4342).</summary>
        public double Radius;
        /// <summary>It is standable on the floor where |x − X| ≤ <see cref="Half"/>, to BaseY + <see cref="Height"/> (<c>surfaceCh1</c>, L4143–L4163).</summary>
        public double Half, Height;
        /// <summary>False: never standable (a coat, a pole).</summary>
        public bool Solid = true;
        /// <summary>How far below his wrists it hangs (<c>it.below</c>, L4261–L4268).</summary>
        public double BelowWrist = 0.28;
        /// <summary>Light: he walks, jumps and climbs with it (the playtest of 23 Oct, L1967–L1969).</summary>
        public bool IsLight;
        /// <summary>From this checkpoint it starts somewhere else (a solved state, §4.28); null = always at home.</summary>
        public string MovedAfter;
        public ItemState MovedState = ItemState.Placed;
        public double MovedX, MovedBaseY;
        public int MovedSlot = -1;

        /// <summary>DL-02's parcel box: 0.40 × 0.20 at x 17.4 on the floor (<c>SH.boxX</c> L3888; <c>itemsHere</c> L4261 h 0.2, r 0.2, BAIL_BELOW_WRIST; surface L4150).</summary>
        public static CarriedItemParams Dl02Box() => new CarriedItemParams
        {
            HomeX = 17.4, HomeBaseY = 0,                                                  // SH.boxX, L3888; resetCh1 L4095
            Radius = 0.2, Half = 0.2, Height = 0.2,                                       // L4261, L4150
            BelowWrist = 0.28,                                                            // BAIL_BELOW_WRIST, L320
        };
    }

    /// <summary>
    /// A thing D-17 lifts, carries and sets down (§4.10; Core <c>CarriedItem</c>): DL-02's box, DL-03's weight, the
    /// suitcase and plates of DL-08–10, chapter 1's coat and pole. Implements U-11's <see cref="ICarryable"/>: the motor
    /// runs the Lift and SetDown clips and calls <see cref="OnLifted"/> (f22) and <see cref="OnSetDown"/> (f14), which only
    /// record what happened; <see cref="Step"/> applies it. A receiver (an <see cref="IPlaceTarget"/>, a carrier) moves it
    /// with <see cref="MoveTo"/>. Lane: <see cref="CarriedItemLane"/>. Plates weigh it as an <see cref="IPlateBody"/>.
    /// Signals: <see cref="Position"/> = x, metres.
    /// </summary>
    public sealed class CarriedItem : Mechanism, ICarryable, IPlateBody, IPositionSource
    {
        /// <summary>The view drops a set-down item to its rest over 0.2 s (<c>placeItem</c>, L4972).</summary>
        public const double DropSeconds = 0.2;

        private readonly CarriedItemParams _p;
        private bool _lift, _down, _move;
        private double _downX, _downY, _moveX, _moveY;
        private ItemState _moveState;
        private int _moveSlot;

        public CarriedItem(MechanismId id, CarriedItemParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            X = p.HomeX; BaseY = p.HomeBaseY; Slot = -1;
        }

        public CarriedItemParams Params => _p;
        public ItemState State => (ItemState)StateCode;
        /// <summary>The receiver's slot while <see cref="ItemState.Placed"/> (else −1).</summary>
        public int Slot { get; private set; }
        /// <summary>Seconds since it was last set down (the view's drop); ≥ <see cref="DropSeconds"/> = at rest.</summary>
        public double SinceSetDown { get; private set; } = DropSeconds;

        // ---- ICarryable --------------------------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Item;
        public double X { get; private set; }
        public double BaseY { get; private set; }
        public double Radius => _p.Radius;
        public double BelowWrist => _p.BelowWrist;
        public bool IsLight => _p.IsLight;

        /// <summary>Only from the floor (<c>it.state !== 'floor'</c> skips it, L4217).</summary>
        public bool IsAvailable(in InteractionQuery q) => State == ItemState.Floor;
        public void OnLifted() => _lift = true;
        public void OnSetDown(double x, double baseY) { _down = true; _downX = x; _downY = baseY; }

        /// <summary>A receiver takes it (or a carrier tips it, or it is lost): applied at the next <see cref="Step"/>.</summary>
        public void MoveTo(ItemState state, double x, double baseY, int slot = -1)
        {
            _move = true; _moveState = state; _moveX = x; _moveY = baseY; _moveSlot = slot;
        }

        /// <summary>
        /// He dropped it where he stood, at once (a death's <c>releaseHolds</c>, L7425–L7428: <c>state 'floor'</c>, his x,
        /// <c>max(0, y)</c>). It runs inside the hazards' step in the prototype, so it is applied now, unlogged, rather than
        /// at the next <see cref="Step"/>. Only an item in his hands drops.
        /// </summary>
        public void Drop(double x, double baseY)
        {
            if (State != ItemState.Carried) return;
            Init((int)ItemState.Floor);
            X = x; BaseY = baseY; Slot = -1;
            SinceSetDown = DropSeconds;                                                   // drop: null, it is simply there
            _lift = _down = _move = false;
        }

        // ---- IPlateBody / IPositionSource ----------------------------------------------------------------------------
        public double SupportX => X;
        public BodySupport Support
        {
            get
            {
                switch (State)
                {
                    case ItemState.Floor: return BodySupport.Floor;
                    case ItemState.Carried: return BodySupport.Carried;
                    case ItemState.Placed: return BodySupport.Placed;
                    case ItemState.InCarrier: return BodySupport.Carrier;
                    default: return BodySupport.Away;
                }
            }
        }
        public double Position => X;

        /// <summary>
        /// The top D-17 can stand on at <paramref name="x"/>, or NaN: on the floor and solid, |x − X| ≤ Half
        /// (<c>surfaceCh1</c>: the box L4150, the weight L1726).
        /// </summary>
        public double TopAt(double x)
            => _p.Solid && State == ItemState.Floor && Math.Abs(x - X) <= _p.Half ? BaseY + _p.Height : double.NaN;

        public override void Reset(in Checkpoint cp)
        {
            bool moved = cp.Past(_p.MovedAfter);
            Init((int)(moved ? _p.MovedState : ItemState.Floor));
            X = moved ? _p.MovedX : _p.HomeX;
            BaseY = moved ? _p.MovedBaseY : _p.HomeBaseY;
            Slot = moved && _p.MovedState == ItemState.Placed ? _p.MovedSlot : -1;
            SinceSetDown = DropSeconds;
            _lift = _down = _move = false;
        }

        public override void Step(in StepContext ctx)
        {
            if (SinceSetDown < DropSeconds) SinceSetDown += ctx.Dt;
            if (_lift)
            {
                _lift = false;
                if (State == ItemState.Floor) { Enter(ctx, (int)ItemState.Carried); Slot = -1; Emit(ctx, (int)ItemEvent.Lifted, 0, X); }   // L4419
            }
            if (_down)
            {
                _down = false;
                X = _downX; BaseY = _downY; Slot = -1; SinceSetDown = 0;                                           // L4425
                Enter(ctx, (int)ItemState.Floor);
                Emit(ctx, (int)ItemEvent.SetDown, 0, X);
            }
            if (_move)
            {
                _move = false;
                X = _moveX; BaseY = _moveY; Slot = _moveState == ItemState.Placed ? _moveSlot : -1;
                Enter(ctx, (int)_moveState);
                Emit(ctx, (int)ItemEvent.Moved, (int)_moveState, X);
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("base", BaseY); w.WriteLong("slot", Slot); w.WriteDouble("since", SinceSetDown);
            w.WriteBool("lift", _lift); w.WriteBool("down", _down); w.WriteDouble("downX", _downX); w.WriteDouble("downY", _downY);
            w.WriteBool("move", _move); w.WriteLong("moveState", (int)_moveState); w.WriteDouble("moveX", _moveX); w.WriteDouble("moveY", _moveY);
            w.WriteLong("moveSlot", _moveSlot);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); BaseY = r.ReadDouble("base"); Slot = (int)r.ReadLong("slot"); SinceSetDown = r.ReadDouble("since");
            _lift = r.ReadBool("lift"); _down = r.ReadBool("down"); _downX = r.ReadDouble("downX"); _downY = r.ReadDouble("downY");
            _move = r.ReadBool("move"); _moveState = (ItemState)r.ReadLong("moveState"); _moveX = r.ReadDouble("moveX"); _moveY = r.ReadDouble("moveY");
            _moveSlot = (int)r.ReadLong("moveSlot");
        }
    }
}
