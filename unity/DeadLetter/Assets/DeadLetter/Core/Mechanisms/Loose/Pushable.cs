using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Loose
{
    public enum PushableState
    {
        /// <summary>On the floor, free to push (<c>state 'free'</c>).</summary>
        Free,
        /// <summary>In his hands (<c>game.hold === 'push'</c>): it weighs as on the floor.</summary>
        Held,
        /// <summary>Reached its end of travel and stays (courier → cradle, drum → set, body → plate; L4723–L4735).</summary>
        Done,
    }

    public enum PushableEvent
    {
        /// <summary>He let go (Jump, Use, a detent, an escort). Value = x.</summary>
        Released,
        /// <summary>It reached Max and is done (<see cref="PushableParams.DoneAtMax"/>). Value = x.</summary>
        TravelEnd,
    }

    public sealed class PushableParams
    {
        /// <summary>Where it stands at the start, and from <see cref="MovedAfter"/> on.</summary>
        public double StartX;
        public string MovedAfter;
        public double MovedX;
        /// <summary>He stands at x − Side·Gap facing Side; <see cref="TwoSided"/> adds the twin from the other side (pass 10, L4287–L4295).</summary>
        public int Side = +1;
        public bool TwoSided;
        public double Gap = 0.6, Speed = 0.4;
        /// <summary>Speed with something on its deck (DL-03: <c>PUSH_LOADED</c> 0.42, L325); NaN = <see cref="Speed"/>.</summary>
        public double LoadedSpeed = double.NaN;
        /// <summary>m/s²: 1.4 for chapter 1's pushables (L4690); the old holds 3 (DL-03 trolley) and 1.3 (DL-08, DL-11 desk), L2332.</summary>
        public double Accel = 1.4;
        public double Min, Max;
        /// <summary>While this <see cref="IEngageable"/> is engaged, Max is <see cref="AltMax"/> (DL-08: latched, to the rail, L2341).</summary>
        public MechanismId AltMaxWhen;
        public double AltMax;
        public double FloorY, Z, ForwardReach = 0.34, BackReach = 0.34;
        public bool HasDetents;
        /// <summary>He lets go at Max (chapter 1's pushables, L4723–L4735); false for the old holds, which stop there in his hands (L2338–L2346).</summary>
        public bool LetGoAtMax = true;
        /// <summary>At Max it is done (stays, no longer pushable) and <see cref="PushableEvent.TravelEnd"/> fires; from DoneAfter it starts done at Max.</summary>
        public bool DoneAtMax;
        public string DoneAfter;
        /// <summary>Its body in the lane: half-length, and the solid top above its floor (0 = not solid); the top only within Half − SolidInset (L1726, L1731).</summary>
        public double Half, Height, SolidInset;
        /// <summary>
        /// Things on the floor it stops against (each an <see cref="IPlateBody"/>), at <see cref="BlockGap"/> centre to centre
        /// (L2342–L2346). A blocker that is a <c>Carryable</c> riding this deck is also what makes it <see cref="Pushable.Loaded"/>.
        /// </summary>
        public MechanismId[] Blockers = Array.Empty<MechanismId>();
        public double BlockGap;
        /// <summary>A deck he can set a carryable on (0 = none): its top above the floor, and how far off centre a thing may sit (L2268–L2272).</summary>
        public double DeckHeight, DeckOffsetMax = 0.17, DeckMargin = 0.02;

        /// <summary>
        /// DL-03: the trolley, pushed from either end (grabL/grabR, gap 0.62), 0.55 m/s (0.42 loaded), acc 3, in the room
        /// 25.44–29.97, solid to its deck (0.16), stops against the weight on the floor, carries the weight on its deck;
        /// parked on the plate from <c>solved</c> (L321–L325, L2241–L2346, L8026).
        /// </summary>
        public static PushableParams Dl03Trolley() => new PushableParams
        {
            StartX = 13 + 14.55, MovedAfter = "solved", MovedX = (13 + 15.8 + 13 + 16.55) / 2,   // TROLLEY_X; the plate's middle
            Side = +1, TwoSided = true, Gap = 0.62, Speed = 0.55, LoadedSpeed = 0.42, Accel = 3,      // PUSH_GAP, PUSH_SPEED/LOADED, L2332
            Min = 13 + 12.1 + 0.06 + 0.28, Max = 13 + 17.6 - 0.35 - 0.28,                             // TROLLEY_MIN/MAX, L322
            Half = 0.28, Height = 0.16,                                                               // TROLLEY_HALF/DECK, L321
            Blockers = new MechanismId[] { "dl03.weight" }, BlockGap = 0.28 + 0.1 + 0.01,             // L2342
            DeckHeight = 0.16, LetGoAtMax = false,
        };

        /// <summary>
        /// DL-08: the goods trolley on the deck (1.6), pushed from either end (gap 0.70), 0.34 m/s, acc 1.3, 81.95–84.5; with the
        /// platform latched it runs on to the rail (88.22); solid to its ballast (0.44, inset 0.04); at T4_MAX from <c>latched</c>
        /// (L3008–L3009, L1731, L2332, L2341, L3897, L8042).
        /// </summary>
        public static PushableParams Dl08Trolley() => new PushableParams
        {
            StartX = 33 + 49.5, MovedAfter = "latched", MovedX = 33 + 51.9 - 0.04 - 0.36,             // T4_X; T4_MAX
            Side = +1, TwoSided = true, Gap = 0.7, Speed = 0.34, Accel = 1.3,                         // PUSH_GAP4, PUSH_HEAVY
            Min = 33 + 48.95, Max = 33 + 51.9 - 0.04 - 0.36,
            AltMaxWhen = "dl08.pawl", AltMax = 33 + 55.6 - 0.36 - 0.02,                               // RAIL7.x0 − T4_HALF − 0.02
            FloorY = 1.6, Half = 0.36, Height = 0.44, SolidInset = 0.04,                              // DECK, T4_HALF, T4_TOP
            LetGoAtMax = false,
        };
    }

    /// <summary>
    /// A generic push/pull/drag object (§4.11; the old holds L2318–L2362 and chapter 1's <c>PUSHABLES</c> L4273–L4304,
    /// L4683–L4735): an <see cref="IPushable"/> (and its twin from the other side, <see cref="Twin"/>) that is also an
    /// <see cref="IPlateBody"/>, so plates weigh it; it can stop against things on the floor, carry a carryable on its
    /// deck (<see cref="DeckTarget"/>, an <see cref="IPlaceTarget"/>), run faster or slower loaded, and end its travel.
    /// The pushables that tip into pits stay <see cref="Bridges.TippingBridge"/>. The motor moves it while held
    /// (<see cref="MoveTo"/>, applied at once as the prototype's <c>t.x = tx</c>). Register <see cref="DeckTarget"/> and
    /// <see cref="Twin"/> with the resolver as well. The lane sees it through <c>Scenes.PushableLane</c>.
    /// Signals: <see cref="IPlateBody"/>; <see cref="IPositionSource.Position"/> = x.
    /// </summary>
    public sealed class Pushable : Mechanism, IPushable, IPlateBody, IPositionSource
    {
        private readonly PushableParams _p;
        private IPlateBody[] _blockers = Array.Empty<IPlateBody>();
        private IEngageable _altMax;
        private bool _held, _released, _ended;

        public Pushable(MechanismId id, PushableParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            Twin = p.TwoSided ? new PushTwin(this) : null;
            DeckTarget = p.DeckHeight > 0 ? new PushableDeck(this) : null;
        }

        public PushableState State => (PushableState)StateCode;
        public PushableParams Params => _p;
        /// <summary>The same thing gripped from the other end (Side −Side), or null.</summary>
        public IPushable Twin { get; }
        /// <summary>Its deck as a context set-down, or null.</summary>
        public PushableDeck DeckTarget { get; }
        /// <summary>The deck's top (where a carryable on it rests).</summary>
        public double DeckTop => _p.FloorY + _p.DeckHeight;
        public double Velocity { get; private set; }
        /// <summary>Something rides its deck.</summary>
        public bool Loaded
        {
            get { for (int i = 0; i < _blockers.Length; i++) if (_blockers[i] is Carryable c && ReferenceEquals(c.Deck, this)) return true; return false; }
        }

        // ---- IPushable -----------------------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Push;
        public double X { get; private set; }
        public int Side => _p.Side;
        public double Gap => _p.Gap;
        public double Speed => Loaded && !double.IsNaN(_p.LoadedSpeed) ? _p.LoadedSpeed : _p.Speed;   // L2335
        public double Accel => _p.Accel;
        public double FloorY => _p.FloorY;
        public double Z => _p.Z;
        public double ForwardReach => _p.ForwardReach;
        public double BackReach => _p.BackReach;
        public bool TipsIntoPit => false;
        public bool HasDetents => _p.HasDetents;
        public bool LetGoAtMax => _p.LetGoAtMax;

        /// <summary>Its start, or the far side of a blocker on the floor to its left (L2346).</summary>
        public double Min
        {
            get
            {
                double m = _p.Min;
                for (int i = 0; i < _blockers.Length; i++)
                {
                    var b = _blockers[i];
                    if (b.Support == BodySupport.Floor && b.X < X) m = Math.Max(m, b.X + _p.BlockGap);
                }
                return m;
            }
        }

        /// <summary>Its end of travel (or the rail's, once <see cref="PushableParams.AltMaxWhen"/> holds), or short of a blocker to its right (L2341–L2345).</summary>
        public double Max
        {
            get
            {
                double m = _altMax != null && _altMax.Engaged ? _p.AltMax : _p.Max;
                for (int i = 0; i < _blockers.Length; i++)
                {
                    var b = _blockers[i];
                    if (b.Support == BodySupport.Floor && b.X > X) m = Math.Min(m, b.X - _p.BlockGap);
                }
                return m;
            }
        }

        /// <summary>Free (<c>state 'free'</c>, L4296) and on its floor.</summary>
        public bool IsAvailable(in InteractionQuery q) => State != PushableState.Done;

        public void MoveTo(double x, double velocity) { X = x; Velocity = velocity; _held = true; }
        public void SetAtLip(bool atLip) { }
        public void OnReleased(bool atLip) { _released = true; Velocity = 0; }
        public void OnShoved() { _released = true; }
        public void OnTravelEnd() { if (_p.DoneAtMax) _ended = true; }

        // ---- IPlateBody / IPositionSource ----------------------------------------------------------------------------
        public double SupportX => X;
        public BodySupport Support => State == PushableState.Held ? BodySupport.Pushed : BodySupport.Floor;
        public double Position => X;

        public override void Link(MechanismLinker link)
        {
            _blockers = new IPlateBody[_p.Blockers.Length];
            for (int i = 0; i < _blockers.Length; i++)
                _blockers[i] = link.ReadAnyOrder<IPlateBody>(_p.Blockers[i]) ?? throw new InvalidOperationException(Id + ": blocker " + i + " is unwired.");
            _altMax = link.ReadAnyOrder<IEngageable>(_p.AltMaxWhen);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool done = cp.Past(_p.DoneAfter);
            Init((int)(done ? PushableState.Done : PushableState.Free));
            X = done ? _p.Max : cp.Past(_p.MovedAfter) ? _p.MovedX : _p.StartX;
            Velocity = 0;
            _held = _released = _ended = false;
        }

        public override void Step(in StepContext ctx)
        {
            if (_ended)
            {
                Enter(ctx, (int)PushableState.Done);
                Emit(ctx, (int)PushableEvent.TravelEnd, 0, X);
            }
            else if (_released && State == PushableState.Held)
            {
                Enter(ctx, (int)PushableState.Free);
                Emit(ctx, (int)PushableEvent.Released, 0, X);
            }
            else if (_held && State == PushableState.Free) Enter(ctx, (int)PushableState.Held);
            if (!_held) Velocity = 0;
            _held = _released = _ended = false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("v", Velocity);
            w.WriteBool("held", _held); w.WriteBool("released", _released); w.WriteBool("ended", _ended);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); Velocity = r.ReadDouble("v");
            _held = r.ReadBool("held"); _released = r.ReadBool("released"); _ended = r.ReadBool("ended");
        }

        /// <summary>The same pushable gripped from its other end (pass 10's twins share state, L4287–L4295).</summary>
        private sealed class PushTwin : IPushable
        {
            private readonly Pushable _o;
            public PushTwin(Pushable o) { _o = o; }
            public InteractionCategory Category => InteractionCategory.Push;
            public bool IsAvailable(in InteractionQuery q) => _o.IsAvailable(q);
            public double X => _o.X;
            public int Side => -_o.Side;
            public double Gap => _o.Gap;
            public double Speed => _o.Speed;
            public double Accel => _o.Accel;
            public double Min => _o.Min;
            public double Max => _o.Max;
            public double FloorY => _o.FloorY;
            public double Z => _o.Z;
            public double ForwardReach => _o.ForwardReach;
            public double BackReach => _o.BackReach;
            public bool TipsIntoPit => false;
            public bool HasDetents => _o.HasDetents;
            public bool LetGoAtMax => _o.LetGoAtMax;
            public void MoveTo(double x, double velocity) => _o.MoveTo(x, velocity);
            public void SetAtLip(bool atLip) { }
            public void OnReleased(bool atLip) => _o.OnReleased(atLip);
            public void OnShoved() => _o.OnShoved();
            public void OnTravelEnd() => _o.OnTravelEnd();
        }
    }

    /// <summary>
    /// A pushable's deck as a context set-down (DL-03: the weight onto the trolley, <c>beginSetDown</c>, L2265–L2273): it
    /// answers when the spot GRIP_FWD in front of him is over the deck (half + 0.02); he sets down where he stands, with
    /// <c>SetDownHigh</c>, at an offset clamped to ±0.17 of its middle. Category Item.
    /// </summary>
    public sealed class PushableDeck : IPlaceTarget
    {
        private readonly Pushable _o;
        private readonly double _grip;

        internal PushableDeck(Pushable o, double gripForward = 0.29) { _o = o; _grip = gripForward; }

        public InteractionCategory Category => InteractionCategory.Item;
        public string Clip => ClipNames.SetDownHigh;
        public bool TurnIntoSet => false;
        /// <summary>The offset the last <see cref="Offer"/> answered with (read by the carryable when it is placed).</summary>
        public double LastOffset { get; private set; }

        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            pose = default;
            if (_o.State == PushableState.Done) return false;
            double tx = q.X + q.Facing * _grip, d = tx - _o.X;                                       // L2266–L2267
            var pp = _o.Params;
            if (!(Math.Abs(d) <= pp.Half + pp.DeckMargin) || Math.Abs(q.Y - pp.FloorY) >= 0.05) return false;
            LastOffset = Math.Max(-pp.DeckOffsetMax, Math.Min(pp.DeckOffsetMax, d));                // L2272
            pose = new StationPose(q.X, q.Facing, 0, _o.X);
            return true;
        }

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);
        public bool Accepts(ICarryable item) => item is Carryable c && c.Rides(_o);
        public void OnPlaced(ICarryable item) { }
    }
}
