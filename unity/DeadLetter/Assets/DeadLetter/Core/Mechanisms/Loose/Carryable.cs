using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Loose
{
    public enum CarryableState
    {
        /// <summary>Resting on the lane (<c>'floor'</c>): liftable; solid in the lane if it is (the weight, the box).</summary>
        Rest,
        /// <summary>In his hands (<c>'carried'</c>): it weighs with him.</summary>
        Carried,
        /// <summary>Riding a pushable's deck (<c>'trolley'</c>, DL-03): it moves and weighs with the deck.</summary>
        OnDeck,
        /// <summary>Set into a receiver that is not a deck (tray, carrier, car, peg): the receiver owns it now.</summary>
        Placed,
    }

    public enum CarryableEvent
    {
        /// <summary>Lift f22: it leaves its rest (<c>Sound.scrape</c>, L2283, L4417).</summary>
        Lifted,
        /// <summary>SetDown f14: it rests on the lane (<c>Sound.setDown</c>, L2288, L4425). Value = x.</summary>
        SetDown,
        /// <summary>SetDown f14 into a receiver (Index 1 = onto a deck). Value = x.</summary>
        Placed,
    }

    public sealed class CarryableParams
    {
        /// <summary>Where it rests at the start: lane x and the height it rests on.</summary>
        public double X, BaseY;
        /// <summary>Half-width (set-down flatness test and lane extent), height, hang below the wrists (§4.10, L4261–L4268).</summary>
        public double Radius = 0.1, Height = 0.22, BelowWrist = 0.28;
        /// <summary>Light (coat, pole, tin): carried at a walk, jumps allowed (L1967–L1970).</summary>
        public bool Light;
        /// <summary>Solid in the lane while it rests: its top (base + Height) is standable within Radius (L1726, L4150, L4153).</summary>
        public bool Solid = true;
        /// <summary>Solid only for a probe already at its base level (|h − base| &lt; 0.05: the plates and the case, L4153, L4156).</summary>
        public bool SolidAtBaseOnly;
        /// <summary>The pushables (by ID) whose deck it may be set on (DL-03: the trolley).</summary>
        public MechanismId[] Decks = Array.Empty<MechanismId>();
        /// <summary>From this checkpoint on it starts moved (§4.28): on deck <see cref="MovedDeck"/> at <see cref="MovedOffset"/>, or resting at (MovedX, MovedBaseY).</summary>
        public string MovedAfter;
        public int MovedDeck = -1;
        public double MovedOffset, MovedX, MovedBaseY;

        /// <summary>DL-02: the box by the slot, h 0.2, r 0.2 (<c>SH.boxX</c>, L3887, L4095, L4150, L4261).</summary>
        public static CarryableParams Dl02Box() => new CarryableParams { X = 17.4, Radius = 0.2, Height = 0.2, BelowWrist = 0.28 };

        /// <summary>
        /// DL-03: the weight by its stand (<c>WEIGHT_X</c> = OFF2 + 12.62, r 0.1, h 0.22, L320); it rides the trolley's deck;
        /// from <c>solved</c> it is on the deck 0.12 left of the trolley's middle (L8025).
        /// </summary>
        public static CarryableParams Dl03Weight() => new CarryableParams
        {
            X = 13 + 12.62, Radius = 0.1, Height = 0.22, BelowWrist = 0.28,
            Decks = new MechanismId[] { "dl03.trolley" },
            MovedAfter = "solved", MovedDeck = 0, MovedOffset = -0.12,
        };
    }

    /// <summary>
    /// A loose thing he lifts, carries and sets down (§4.10; the DL-03 weight L2229–L2316, chapter 1's items L4259–L4428):
    /// a generic <see cref="ICarryable"/> that is also an <see cref="IPlateBody"/>, so plates and docks weigh it where it
    /// rests, in his hands, on a deck or in a receiver (<see cref="BodySupport"/>). The motor's callbacks are recorded and
    /// applied in Step (add it after the decks it rides). The lane sees it through <c>Scenes.CarryableLane</c>.
    /// Signals: <see cref="IPlateBody"/>; <see cref="IPositionSource.Position"/> = x.
    /// </summary>
    public sealed class Carryable : Mechanism, ICarryable, IPlateBody, IPositionSource
    {
        private enum Pending { None, Lift, SetDown, Deck, Placed }

        private readonly CarryableParams _p;
        private Pushable[] _decks = Array.Empty<Pushable>();
        private double _x, _base, _off, _heldX;
        private int _deck = -1;
        private Pending _pending;
        private double _pendX, _pendBase, _pendOff;
        private int _pendDeck = -1;

        public Carryable(MechanismId id, CarryableParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
        }

        public CarryableState State => (CarryableState)StateCode;
        public CarryableParams Params => _p;
        /// <summary>The deck it rides, or null.</summary>
        public Pushable Deck => State == CarryableState.OnDeck && _deck >= 0 ? _decks[_deck] : null;

        // ---- ICarryable ----------------------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Item;
        public double X => State == CarryableState.Carried ? _heldX : State == CarryableState.OnDeck ? Deck.X + _off : _x;
        public double BaseY => State == CarryableState.OnDeck ? Deck.DeckTop : _base;
        public double Radius => _p.Radius;
        public double BelowWrist => _p.BelowWrist;
        public bool IsLight => _p.Light;
        /// <summary>Liftable while it rests on the lane (DL-03: <c>w.state === 'floor'</c>, L2251).</summary>
        public bool IsAvailable(in InteractionQuery q) => State == CarryableState.Rest;
        public void OnLifted() => _pending = Pending.Lift;
        public void OnSetDown(double x, double baseY) { _pending = Pending.SetDown; _pendX = x; _pendBase = baseY; }

        public void OnPlaced(IPlaceTarget target)
        {
            for (int i = 0; i < _decks.Length; i++)
                if (_decks[i] != null && ReferenceEquals(_decks[i].DeckTarget, target))
                {
                    _pending = Pending.Deck; _pendDeck = i; _pendOff = _decks[i].DeckTarget.LastOffset;
                    return;
                }
            _pending = Pending.Placed;
            _pendX = _heldX;
        }

        /// <summary>It may ride <paramref name="deck"/>'s deck.</summary>
        public bool Rides(Pushable deck)
        {
            for (int i = 0; i < _decks.Length; i++) if (ReferenceEquals(_decks[i], deck)) return true;
            return false;
        }

        // ---- IPlateBody / IPositionSource ----------------------------------------------------------------------------
        public double SupportX => State == CarryableState.OnDeck ? Deck.X : X;
        public BodySupport Support => State == CarryableState.Rest ? BodySupport.Floor : State == CarryableState.Carried ? BodySupport.Carried
            : State == CarryableState.OnDeck ? BodySupport.Carrier : BodySupport.Placed;
        public double Position => X;

        public override void Link(MechanismLinker link)
        {
            _decks = new Pushable[_p.Decks.Length];
            for (int i = 0; i < _decks.Length; i++)
                _decks[i] = link.Read<Pushable>(_p.Decks[i]) ?? throw new InvalidOperationException(Id + ": deck " + i + " is unwired.");
        }

        public override void Reset(in Checkpoint cp)
        {
            _pending = Pending.None; _pendDeck = -1;
            _heldX = _p.X;
            if (cp.Past(_p.MovedAfter))
            {
                if (_p.MovedDeck >= 0) { Init((int)CarryableState.OnDeck); _deck = _p.MovedDeck; _off = _p.MovedOffset; _x = _p.X; _base = _p.BaseY; return; }
                Init((int)CarryableState.Rest); _x = _p.MovedX; _base = _p.MovedBaseY; _deck = -1; _off = 0;
                return;
            }
            Init((int)CarryableState.Rest);
            _x = _p.X; _base = _p.BaseY; _deck = -1; _off = 0;
        }

        public override void Step(in StepContext ctx)
        {
            _heldX = ctx.Player.X;
            switch (_pending)
            {
                case Pending.Lift:
                    Enter(ctx, (int)CarryableState.Carried);
                    Emit(ctx, (int)CarryableEvent.Lifted);
                    break;
                case Pending.SetDown:
                    _x = _pendX; _base = _pendBase; _deck = -1;
                    Enter(ctx, (int)CarryableState.Rest);
                    Emit(ctx, (int)CarryableEvent.SetDown, 0, _x);
                    break;
                case Pending.Deck:
                    _deck = _pendDeck; _off = _pendOff;
                    Enter(ctx, (int)CarryableState.OnDeck);
                    Emit(ctx, (int)CarryableEvent.Placed, 1, X);
                    break;
                case Pending.Placed:
                    _x = _pendX; _deck = -1;
                    Enter(ctx, (int)CarryableState.Placed);
                    Emit(ctx, (int)CarryableEvent.Placed, 0, _x);
                    break;
            }
            _pending = Pending.None;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", _x); w.WriteDouble("base", _base); w.WriteDouble("off", _off); w.WriteDouble("heldX", _heldX);
            w.WriteLong("deck", _deck);
            w.WriteLong("pending", (long)_pending); w.WriteDouble("pendX", _pendX); w.WriteDouble("pendBase", _pendBase);
            w.WriteDouble("pendOff", _pendOff); w.WriteLong("pendDeck", _pendDeck);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _x = r.ReadDouble("x"); _base = r.ReadDouble("base"); _off = r.ReadDouble("off"); _heldX = r.ReadDouble("heldX");
            _deck = (int)r.ReadLong("deck");
            if (_deck >= _decks.Length) throw new InvalidOperationException("Snapshot deck " + _deck + " at '" + Id + "' (this build wires " + _decks.Length + ").");
            _pending = (Pending)r.ReadLong("pending"); _pendX = r.ReadDouble("pendX"); _pendBase = r.ReadDouble("pendBase");
            _pendOff = r.ReadDouble("pendOff"); _pendDeck = (int)r.ReadLong("pendDeck");
        }
    }
}
