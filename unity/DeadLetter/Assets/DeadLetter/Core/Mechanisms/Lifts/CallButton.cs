using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    public enum CallButtonState { Idle, Pressing }

    public enum CallButtonEvent
    {
        /// <summary>PressButtonHigh f16: the button goes in (<c>Sound.click</c>) and the lift is asked to go (L4581–L4582).</summary>
        Press,
    }

    public sealed class CallButtonParams
    {
        /// <summary>Where he stands; its reach is wide (the exact answer is <see cref="X0"/>, <see cref="X1"/> and the floor).</summary>
        public Station Station;
        /// <summary>The clip (<c>PressButtonHigh</c>, 36 frames); the lobby's turns to the wall first (L4531–L4540).</summary>
        public ActProfile Profile = new ActProfile(Clip, turnIntoSet: true);
        public const string Clip = "PressButtonHigh";
        /// <summary>The lift it calls (a <see cref="RelocationLift"/>).</summary>
        public MechanismId Lift;
        /// <summary>The counterweight's own panel: he rides it down when it goes (<c>ride10</c>); false = the lobby's (<c>up10</c>).</summary>
        public bool FromCounterweight;
        /// <summary>It answers for X0 &lt; x &lt; X1, standing within <see cref="FloorWithin"/> of <see cref="FloorY"/> (L4233–L4236).</summary>
        public double X0, X1, FloorY, FloorWithin = 0.05;
        /// <summary>
        /// The lift must be at rest at the bottom (<c>uo.d &lt; 0.01 &amp;&amp; uo.phase === 'idle'</c>, the counterweight's panel,
        /// L4236); false: only idle (the lobby's, L4234).
        /// </summary>
        public bool NeedsRest;
        /// <summary>PressButtonHigh: pushed in from f13 to f22, the press at f16, done at f34 (L4580–L4593).</summary>
        public double InFrame = ClipTimings.PressButtonHighEvents.WindowStart, PressFrame = ClipTimings.PressButtonHighEvents.Act,
            OutFrame = ClipTimings.PressButtonHighEvents.WindowEnd, DoneFrame = ClipTimings.PressButtonHighEvents.Done;

        /// <summary>
        /// DL-10: the lobby's UP (<c>up10</c>): on the deck within 0.22 of <c>UO.upStand</c> while the lift is idle (L4234); he
        /// stands at it facing +x, turns to the wall and presses (L4316, L4531–L4540).
        /// </summary>
        public static CallButtonParams Dl10UpButton() => new CallButtonParams
        {
            Station = new Station(standX: 54 + 69.95, reach: 1, face: 1, floorY: 1.6),                       // UO.upStand, OFF5 = 54; DECK
            Lift = "dl10.lift",
            X0 = 54 + 69.95 - 0.22, X1 = 54 + 69.95 + 0.22, FloorY = 1.6,
        };

        /// <summary>
        /// DL-10: the counterweight's service UP (<c>ride10</c>): on the deck on its footplate, <c>UO.cw.x0 + 0.1</c> to
        /// <c>UO.cw.x1</c>, while the lift is at rest at the bottom (L4236); he stands at <c>UO.cw.stand</c> facing +x and presses
        /// without turning (L4317, L4531).
        /// </summary>
        public static CallButtonParams Dl10ServiceUp() => new CallButtonParams
        {
            Station = new Station(standX: 54 + 73.37, reach: 1, face: 1, floorY: 1.6),                       // UO.cw.stand
            Profile = new ActProfile(Clip),
            Lift = "dl10.lift",
            FromCounterweight = true,
            X0 = 54 + 72.85 + 0.1, X1 = 54 + 73.75, FloorY = 1.6,                                           // UO.cw
            NeedsRest = true,
        };
    }

    /// <summary>
    /// A lift's call button (DL-10's two UP buttons, <c>dl10.upButton</c> and <c>dl10.serviceUp</c>; §4.12: PressButtonHigh,
    /// the press at f16, done at f34; L4579–L4597). At f16 it asks the lift to go (<see cref="RelocationLift.PressUp"/>, which
    /// goes or buzzes as its own rule says); at f34 the act is done. It steps before the lift, which reads the press the
    /// same step (the prototype sets <c>uo.phase</c> at #4, before <c>updateUpOnly</c>). Signals: <see cref="Depressed"/>
    /// (the view's 12 mm, <c>uo.pressL</c>/<c>pressS</c>, L4581). What follows a press that sends him down (the ride) is the
    /// scene's: the act ends at f34.
    /// </summary>
    public sealed class CallButton : StationMechanism
    {
        private readonly CallButtonParams _p;
        private RelocationLift _lift;
        private ActInput _act;

        public CallButton(MechanismId id, CallButtonParams p) : base(id, p.Station) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public CallButtonParams Params => _p;
        public CallButtonState State => (CallButtonState)StateCode;
        /// <summary>Pushed in (PressButtonHigh between f13 and f22, L4581).</summary>
        public bool Depressed { get; private set; }

        public override ActProfile Profile => _p.Profile;

        public override void Link(MechanismLinker link)
            => _lift = link.ReadAnyOrder<RelocationLift>(_p.Lift) ?? throw new InvalidOperationException(Id + " needs a Lift.");

        public override void Reset(in Checkpoint cp)
        {
            Init((int)CallButtonState.Idle);
            Depressed = false;
            _act.Clear();
        }

        /// <summary>L4233–L4236: in reach on its floor, and the lift idle (at rest at the bottom, for the counterweight's).</summary>
        protected override bool CanUse(in InteractionQuery q)
            => q.X > _p.X0 && q.X < _p.X1 && Math.Abs(q.Y - _p.FloorY) < _p.FloorWithin
               && (_p.NeedsRest ? _lift.AtRest : _lift.State == RelocationLiftState.Idle);

        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return ActStep.DoneIf(ClipClock.Reached(f.Frame, _p.DoneFrame));                                   // f >= 34, L4593
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active)
            {
                Depressed = false;
                if (State != CallButtonState.Idle) Enter(ctx, (int)CallButtonState.Idle);
                return;
            }
            if (_act.Started) Enter(ctx, (int)CallButtonState.Pressing);
            Depressed = _act.Frame > _p.InFrame && _act.Frame < _p.OutFrame;                                  // L4581
            if (ClipClock.Crossed(_act.PrevFrame, _act.Frame, _p.PressFrame))                                  // f >= 16 && !a.pressed, L4582
            {
                Emit(ctx, (int)CallButtonEvent.Press);
                _lift.PressUp(_p.FromCounterweight);
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("in", Depressed);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Depressed = r.ReadBool("in");
            _act.Read(r);
        }
    }
}
