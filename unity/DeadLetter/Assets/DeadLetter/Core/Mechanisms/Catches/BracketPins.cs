using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Catches
{
    /// <summary>
    /// Where both pins are. Each state places every pin in exactly one of the fork, the tin cup, the clip or his hands
    /// (<see cref="BracketPins.BentPin"/>, <see cref="BracketPins.SparePin"/>), so no pin can be lost.
    /// </summary>
    public enum BracketPinsState
    {
        /// <summary>The bent pin through fork and lug, holding the platform drooping; the spare in its clip. The start.</summary>
        BentSeated,
        /// <summary>The bent pin drawn part-way (a loaded pull): still in the fork, holding nothing, biting; the spare in its clip.</summary>
        BentHalfOut,
        /// <summary>The bent pin in the tin cup; the fork empty; the spare in its clip.</summary>
        ForkEmpty,
        /// <summary>The bent pin in the cup; the spare in his hands.</summary>
        SpareCarried,
        /// <summary>The bent pin in the cup; the spare seated in the fork. Solved.</summary>
        SpareSeated,
    }

    public enum BracketPinsEvent
    {
        /// <summary>A loaded bent pin slides part-way and bites (the platform drops onto the stops: its own Drop).</summary>
        Draw,
        /// <summary>Use on a biting bent pin: a strain, nothing moves.</summary>
        Strain,
        /// <summary>The slack bent pin comes out and drops into the tin cup (clink).</summary>
        Clink,
        /// <summary>He takes the spare from its clip.</summary>
        Taken,
        /// <summary>The spare seats: a clean double click (the scene plays the <c>witness</c> insert and cue <c>held</c>).</summary>
        Seated,
        /// <summary>The spare chatters against the lug (not level): he keeps it.</summary>
        Chatter,
        /// <summary>The bent pin's sound changed: Index = the new <see cref="PinSound"/>.</summary>
        Sound,
    }

    /// <summary>The places a pin can be (DL-19 §3 "The pins").</summary>
    public enum PinPlace { Fork, Cup, Clip, Hands }

    /// <summary>What the bent pin is doing: creaking (loaded), rattling (slack), or quiet.</summary>
    public enum PinSound { Quiet, Creak, Rattle }

    public sealed class BracketPinsParams
    {
        /// <summary>Where he stands to use the bracket (the fork and the clip are 0.05 apart on one post).</summary>
        public Station Station;
        /// <summary>A tug on the pin or the clip: it takes effect at <see cref="EffectFrame"/> and the clip ends at <see cref="EndFrame"/>.</summary>
        public ActProfile Profile = new ActProfile(ClipNames.Tug);
        public double EffectFrame = ClipTimings.TugEvents.Click, EndFrame = ClipTimings.TugEvents.Done;
        /// <summary>The left-end top the pin in the fork holds the platform at: the bent pin (drooping) and the spare (level).</summary>
        public double BentHoldY, SpareHoldY;
        /// <summary>The platform's level band (the marks meet: a pin is slack, the spare seats) and its stops.</summary>
        public double LevelY, LevelTolerance = 0.02, StopsY;
        /// <summary>The platform (<see cref="IPositionSource"/>: its left end's top).</summary>
        public MechanismId Platform;
        /// <summary>From this checkpoint on the spare is seated and the bent pin in the cup.</summary>
        public string SeatedAfter;

        // DL-19 A Repair That Held: docs/scenes/DL-19_a_repair_that_held.md §3 ("The pins", table), §4, §11 BentPin/SparePin. No prototype.

        /// <summary>
        /// DL-19: the bracket at 363.65 (post 1.2–1.65): the bent pin through fork and lug at 1.62, the spare in its clip on
        /// the post's left face (363.6, 1.42), the tin cup under the fork (363.7, 1.3). He stands left of the post, facing
        /// it; with the jack in its pocket (its crank post at 363.35) he reaches over from 363.05–363.45 (a scene decision:
        /// the crank's stand is just left of this one).
        /// </summary>
        public static BracketPinsParams Dl19Pins() => new BracketPinsParams
        {
            Station = new Station(standX: 363.25, reach: 0.2, face: +1, floorY: 1.2, reachX: 363.25),   // §3 "Bracket", terrace landing 1.2
            BentHoldY = 1.55, SpareHoldY = 1.75,                    // §3 states: drooping 1.55; pinned on the spare 1.75
            LevelY = 1.75, LevelTolerance = 0.02, StopsY = 1.45,    // §3 states: level 1.75 ± 0.02; the stops 1.45
            Platform = "dl19.landing",
            SeatedAfter = "repaired",                               // §9: repaired, with the half landing pinned
        };
    }

    /// <summary>
    /// The bracket's pins (chapter2_plan §7 "Brakes and catches"; DL-19 §3 "The pins", §4, §11 <c>BentPin</c>,
    /// <c>SparePin</c>): one station at the bracket post, where Use does the one thing the pins allow. A bent pin in the
    /// fork is drawn: loaded (the platform off its level band) it slides part-way and bites, so the platform drops onto
    /// its stops, and another Use only strains; slack (level) it comes out into the tin cup. With the fork empty, Use takes
    /// the spare from its clip; holding it, Use seats it if the marks meet and otherwise it chatters and he keeps it. So the
    /// spare is taken only once the bent pin is out (the clip and the fork are 5 cm apart on one post; a deliberate
    /// simplification: one Use spot, never two answering at once). The spare "in his hands" is this mechanism's state:
    /// the motor's hold stays empty. A reset before <see cref="BracketPinsParams.SeatedAfter"/> puts a carried spare back
    /// in its clip. No prototype exists; the type is new for chapter 2.
    /// <para>Signals: <see cref="Position"/> = the left-end top the pin in the fork holds the platform at, metres
    /// (−∞ when it holds nothing); <see cref="Engaged"/> = the spare is seated.</para>
    /// </summary>
    public sealed class BracketPins : StationMechanism, IPositionSource, IEngageable
    {
        private const double Eps = 1e-9;

        private readonly BracketPinsParams _p;
        private IPositionSource _platform;
        private ActInput _act;
        private bool _done;

        public BracketPins(MechanismId id, BracketPinsParams p) : base(id, p.Station) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public BracketPinsState State => (BracketPinsState)StateCode;
        public double Position
        {
            get
            {
                switch (State)
                {
                    case BracketPinsState.BentSeated: return _p.BentHoldY;
                    case BracketPinsState.SpareSeated: return _p.SpareHoldY;
                    default: return double.NegativeInfinity;
                }
            }
        }
        public bool Engaged => State == BracketPinsState.SpareSeated;
        /// <summary>The bent pin's sound now (the creak while loaded, the rattle while slack).</summary>
        public PinSound Sound { get; private set; }

        /// <summary>Where the bent pin is: the fork (seated or half out) or the tin cup.</summary>
        public PinPlace BentPin => State == BracketPinsState.BentSeated || State == BracketPinsState.BentHalfOut ? PinPlace.Fork : PinPlace.Cup;
        /// <summary>The bent pin is drawn part-way (still in the fork).</summary>
        public bool BentHalfOut => State == BracketPinsState.BentHalfOut;
        /// <summary>Where the spare is: its clip, his hands or the fork.</summary>
        public PinPlace SparePin
            => State == BracketPinsState.SpareCarried ? PinPlace.Hands : State == BracketPinsState.SpareSeated ? PinPlace.Fork : PinPlace.Clip;

        public override ActProfile Profile => _p.Profile;

        public override void Link(MechanismLinker link)
            => _platform = link.ReadAnyOrder<IPositionSource>(_p.Platform) ?? throw new InvalidOperationException(Id + " needs its platform.");

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(cp.Past(_p.SeatedAfter) ? BracketPinsState.SpareSeated : BracketPinsState.BentSeated));   // a carried spare is back in its clip
            Sound = PinSound.Quiet;
            _done = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => State != BracketPinsState.SpareSeated;

        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return ActStep.DoneIf(ClipClock.Reached(f.Frame, _p.EndFrame));
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (_act.Active)
            {
                if (_act.Started) _done = false;
                if (!_done && ClipClock.Reached(_act.Frame, _p.EffectFrame)) { _done = true; Apply(ctx); }
            }

            var sound = SoundNow();
            if (sound != Sound) { Sound = sound; Emit(ctx, (int)BracketPinsEvent.Sound, (int)sound); }
        }

        private bool Level => Math.Abs(_platform.Position - _p.LevelY) <= _p.LevelTolerance + Eps;

        private void Apply(in StepContext ctx)
        {
            bool level = Level;
            switch (State)
            {
                case BracketPinsState.BentSeated:
                    if (level) { Enter(ctx, (int)BracketPinsState.ForkEmpty); Emit(ctx, (int)BracketPinsEvent.Clink); }
                    else { Enter(ctx, (int)BracketPinsState.BentHalfOut); Emit(ctx, (int)BracketPinsEvent.Draw); }
                    break;
                case BracketPinsState.BentHalfOut:
                    if (level) { Enter(ctx, (int)BracketPinsState.ForkEmpty); Emit(ctx, (int)BracketPinsEvent.Clink); }
                    else Emit(ctx, (int)BracketPinsEvent.Strain);
                    break;
                case BracketPinsState.ForkEmpty:
                    Enter(ctx, (int)BracketPinsState.SpareCarried);
                    Emit(ctx, (int)BracketPinsEvent.Taken);
                    break;
                case BracketPinsState.SpareCarried:
                    if (level) { Enter(ctx, (int)BracketPinsState.SpareSeated); Emit(ctx, (int)BracketPinsEvent.Seated); }
                    else Emit(ctx, (int)BracketPinsEvent.Chatter);
                    break;
            }
        }

        /// <summary>
        /// A bent pin in the fork rattles while the platform is level, and creaks while it is lifted off the stops and not
        /// level (it hangs on the pin, or the jack bends it); on the stops, or with no bent pin in the fork, it is quiet.
        /// </summary>
        private PinSound SoundNow()
        {
            if (BentPin != PinPlace.Fork) return PinSound.Quiet;
            if (Level) return PinSound.Rattle;
            return _platform.Position > _p.StopsY + Eps ? PinSound.Creak : PinSound.Quiet;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("sound", (int)Sound);
            w.WriteBool("done", _done);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Sound = (PinSound)r.ReadLong("sound");
            _done = r.ReadBool("done");
            _act.Read(r);
        }
    }
}
