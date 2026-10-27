using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Catches
{
    public enum PawlState { Free, Engaged }

    public enum PawlEvent
    {
        /// <summary>Outside the bite window the dog clatters on the rack's face, twice (LeverStuck f12, f21; L3312–L3313).</summary>
        Clatter,
    }

    public sealed class PawlParams
    {
        public Station Station;
        /// <summary>The mechanism whose position decides the bite (an <see cref="IPositionSource"/>).</summary>
        public MechanismId Source;
        /// <summary>Bite window on the source's position, inclusive.</summary>
        public double BiteMin = double.NegativeInfinity, BiteMax = double.PositiveInfinity;
        public ActProfile BiteProfile = new ActProfile("LeverPull", turnIntoSet: true);
        public ActProfile StuckProfile = new ActProfile("LeverStuck", turnIntoSet: true);
        public double BiteFrame = ClipTimings.LeverEvents.Throw;        // f22, L3318
        public double BiteOutFrame = ClipTimings.LeverEvents.Out;       // f33, L3319
        public double StuckOutFrame = ClipTimings.LeverEvents.StuckDone; // f45, L3314
        public double LeverAway = -18, LeverNear = 6;                   // LEVER_AWAY / LEVER_NEAR, L2460
        public string EngagedAfter;

        /// <summary>DL-08: the safety pawl at Lift 2's landing (L3010, L3269, L3290–L3324).</summary>
        public static PawlParams Dl08Pawl() => new PawlParams
        {
            // PAWL_X = OFF3 + 52.45; reach 0.36 (L3269); on the deck (y ≤ DECK + 0.05, L3267); steps in to PAWL_Z + 0.26
            // = −0.04 (three) = +0.04 (Unity, §0.2).
            Station = new Station(standX: 85.45, reach: 0.36, face: +1, standZ: 0.04, floorY: 1.6),
            Source = "dl08.platform",
            BiteMin = 0.985,                                   // a.stuck = plat.h < 0.985, L3305
            EngagedAfter = "latched",                          // CHECKPOINTS.latched, L7989; resetWorld L8043
        };
    }

    /// <summary>
    /// A pawl worked by a lever act: it bites only while another mechanism's position is inside the bite window
    /// (<c>dl08.pawl</c>: platform h ≥ 0.985). The window is judged when he has stepped in and the clip starts (L3305); inside it, the
    /// lever throws and the pawl engages at f22 (L3316–L3318); outside it the dog rattles (LeverStuck) and nothing holds.
    /// Signals: <see cref="Engaged"/>. The source reads it back (a latched platform stays at the landing, L3180), so the
    /// pawl is added before the source and reads it with ReadAnyOrder (last tick's position, as the prototype's act did).
    /// </summary>
    public sealed class Pawl : StationMechanism, IEngageable
    {
        private readonly PawlParams _p;
        private IPositionSource _source;
        private ActInput _act;
        private bool _stuck, _clipStuck;

        public Pawl(MechanismId id, PawlParams p) : base(id, p.Station) { _p = p; }

        public PawlState State => (PawlState)StateCode;
        public bool Engaged => State == PawlState.Engaged;
        /// <summary>The lever's target angle, degrees; the view eases toward it at rate 8 (L3211).</summary>
        public double LeverDeg { get; private set; }
        /// <summary>How far the dog dips while rattling (<c>pawlDip</c>, L3311).</summary>
        public double Dip { get; private set; }

        /// <summary>True if the source is inside the bite window now.</summary>
        public bool InWindow => _source.Position >= _p.BiteMin && _source.Position <= _p.BiteMax;

        /// <summary>
        /// Asked when Use starts and again at the end of step-in, which decides the clip: <c>a.stuck = plat.h &lt; 0.985</c>
        /// is judged there (L3305), so a platform that reaches the landing while he steps in still bites.
        /// </summary>
        public override ActProfile Profile => InWindow ? _p.BiteProfile : _p.StuckProfile;

        public override void Link(MechanismLinker link) => _source = link.ReadAnyOrder<IPositionSource>(_p.Source)
            ?? throw new InvalidOperationException(Id + " needs a Source.");

        public override void Reset(in Checkpoint cp)
        {
            bool engaged = cp.Past(_p.EngagedAfter);
            Init((int)(engaged ? PawlState.Engaged : PawlState.Free));
            LeverDeg = engaged ? _p.LeverNear : _p.LeverAway;
            Dip = 0;
            _stuck = _clipStuck = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => State == PawlState.Free;   // L3269

        /// <summary>The clip the motor chose at the end of step-in says which it is (LeverStuck or LeverPull, L3305–L3306).</summary>
        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            _clipStuck = f.Clip != null ? f.Clip == _p.StuckProfile.Clip : !InWindow;
            return ActStep.DoneIf(ClipClock.Reached(f.Frame, _clipStuck ? _p.StuckOutFrame : _p.BiteOutFrame));
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active)
            {
                LeverDeg = Engaged ? _p.LeverNear : _p.LeverAway;
                Dip = 0;
                return;
            }
            if (_act.Started) _stuck = _clipStuck;                                                  // L3305
            double f = _act.Frame, prev = _act.PrevFrame;
            if (_stuck)
            {
                double jig = (f > 10 && f < 17 ? Math.Sin((f - 10) * 0.9) : 0) + (f > 19 && f < 26 ? 1.4 * Math.Sin((f - 19) * 0.9) : 0);
                LeverDeg = _p.LeverAway + 6 * Math.Max(0, jig) + 2 * jig;                         // L3310
                Dip = 0.45 * Math.Max(0, jig);
                if (prev <= 12 && f > 12) Emit(ctx, (int)PawlEvent.Clatter, 0);                    // L3312
                if (prev <= 21 && f > 21) Emit(ctx, (int)PawlEvent.Clatter, 1);                    // L3313
            }
            else
            {
                LeverDeg = _p.LeverAway + (_p.LeverNear - _p.LeverAway) * Smooth.Step((f - 10) / 12);   // L3317
                Dip = 0;
                if (State == PawlState.Free && ClipClock.Reached(f, _p.BiteFrame)) Enter(ctx, (int)PawlState.Engaged);   // L3318
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("lever", LeverDeg);
            w.WriteDouble("dip", Dip);
            w.WriteBool("stuck", _stuck);
            w.WriteBool("clipStuck", _clipStuck);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            LeverDeg = r.ReadDouble("lever");
            Dip = r.ReadDouble("dip");
            _stuck = r.ReadBool("stuck");
            _clipStuck = r.ReadBool("clipStuck");
            _act.Read(r);
        }
    }
}
