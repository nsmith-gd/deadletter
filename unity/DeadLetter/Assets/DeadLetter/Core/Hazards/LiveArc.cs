using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Hazards
{
    /// <summary>Where an arc is in its cycle (<c>game.clock % ARC_PERIOD</c>, L7398–L7401).</summary>
    public enum LiveArcState
    {
        /// <summary>Dead.</summary>
        Quiet,
        /// <summary>The tell: a crackle and a flicker (<c>arc.tell</c>).</summary>
        Tell,
        /// <summary>Live (<c>arc.live</c>): touching it is a shock.</summary>
        Live,
    }

    public enum LiveArcEvent
    {
        /// <summary>The tell starts while he is within <see cref="LiveArcParams.NearRange"/> of it: <c>Sound.crackle(0.4)</c> (L7410).</summary>
        Crackle,
        /// <summary>It goes live while he is near: <c>Sound.zap(0.7)</c> (L7409).</summary>
        Zap,
        /// <summary>He is on it while it is live (L7412): emitted on every such step; the scene's rules knock him back or kill him.</summary>
        Touch,
    }

    public sealed class LiveArcParams
    {
        /// <summary>The span it reaches, open ends (<c>x &gt; arc.x0 &amp;&amp; x &lt; arc.x1</c>).</summary>
        public double X0, X1;
        /// <summary>The cycle, seconds (<c>ARC_PERIOD</c>); its phase is the game clock modulo this.</summary>
        public double Period = 2.4;
        /// <summary>[TellStart, TellEnd) and [LiveStart, LiveEnd) in the cycle.</summary>
        public double TellStart, TellEnd, LiveStart, LiveEnd;
        /// <summary>It reaches him while his feet are within <see cref="Band"/> of <see cref="DeckY"/> (L7412).</summary>
        public double DeckY = 1.6, Band = 0.25;
        /// <summary>Its sounds are heard within this of <see cref="X0"/> (<c>near</c>, L7402).</summary>
        public double NearRange = 8;

        /// <summary>DL-09's arc A, from the split insulation: 105.04–105.44, tell 0–0.3 s, live 0.3–0.75 s (<c>ARCS8[0]</c>, L7322).</summary>
        public static LiveArcParams Dl09Arc1() => new LiveArcParams
        {
            X0 = 42 + 63.04, X1 = 42 + 63.44, TellStart = 0, TellEnd = 0.3, LiveStart = 0.3, LiveEnd = 0.75,
        };

        /// <summary>DL-09's arc B, from the frayed end: 105.77–106.17, tell 1.2–1.5 s, live 1.5–1.95 s (<c>ARCS8[1]</c>, L7323).</summary>
        public static LiveArcParams Dl09Arc2() => new LiveArcParams
        {
            X0 = 42 + 63.77, X1 = 42 + 64.17, TellStart = 1.2, TellEnd = 1.5, LiveStart = 1.5, LiveEnd = 1.95,
        };
    }

    /// <summary>
    /// One arc of DL-09's downed cable over the wet patch (§4.14; <c>dl09.arc1</c>, <c>dl09.arc2</c>; <c>ARCS8</c>, L7321–L7324;
    /// <c>updateHazards</c>, L7397–L7414): a pure function of the game clock's phase (<c>game.clock % ARC_PERIOD</c>), so it keeps
    /// its rhythm through deaths and respawns as the prototype's does. The scene binds the game clock
    /// (<see cref="BindClock"/>); unbound (tests), it runs on its own clock from 0. Each step it reports its sounds and whether
    /// D-17 stands in it while it is live (<see cref="LiveArcEvent.Touch"/>); what a touch does (the first one ever knocks him
    /// back, any other kills him, L7413) is the scene rules'. The jagged line, its light and sparks are the view's (they draw
    /// <c>Math.random</c>, which nothing in Core reads). Signals: <see cref="Engaged"/> = live now.
    /// </summary>
    public sealed class LiveArc : Mechanism, IEngageable
    {
        private readonly LiveArcParams _p;
        private Func<double> _clock;
        private double _ownClock;

        public LiveArc(MechanismId id, LiveArcParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (!(p.Period > 0)) throw new ArgumentException("An arc needs a period.");
        }

        public LiveArcParams Params => _p;
        public LiveArcState State => (LiveArcState)StateCode;
        /// <summary>Seconds into the cycle (<c>ta</c>, L7398).</summary>
        public double Phase { get; private set; }
        public bool Engaged => State == LiveArcState.Live;

        /// <summary>The game clock this arc keeps time with (<c>game.clock</c>). Null: its own clock.</summary>
        public void BindClock(Func<double> seconds) => _clock = seconds;

        /// <summary>He is in it at (x, y) (L7412, without the scene's "alive", region and knock-back).</summary>
        public bool Reaches(double x, double y) => x > _p.X0 && x < _p.X1 && Math.Abs(y - _p.DeckY) < _p.Band;

        public override void Reset(in Checkpoint cp)
        {
            Phase = Time() % _p.Period;
            Init((int)StateAt(Phase));
        }

        public override void Step(in StepContext ctx)
        {
            if (_clock == null) _ownClock += ctx.Dt;
            double ta = Phase = Time() % _p.Period;                                                                     // L7398 (JS % = C# %)
            var s = StateAt(ta);
            Enter(ctx, (int)s);
            var pl = ctx.Player;
            bool near = Math.Abs(pl.X - _p.X0) < _p.NearRange;                                                         // L7402
            if (near && s == LiveArcState.Live && ta - ctx.Dt < _p.LiveStart) Emit(ctx, (int)LiveArcEvent.Zap);       // L7409
            if (near && s == LiveArcState.Tell && ta - ctx.Dt < _p.TellStart) Emit(ctx, (int)LiveArcEvent.Crackle);   // L7410
            if (s == LiveArcState.Live && Reaches(pl.X, pl.Y)) Emit(ctx, (int)LiveArcEvent.Touch, 0, pl.X);           // L7412
        }

        private double Time() => _clock != null ? _clock() : _ownClock;

        private LiveArcState StateAt(double ta)
            => ta >= _p.LiveStart && ta < _p.LiveEnd ? LiveArcState.Live : ta >= _p.TellStart && ta < _p.TellEnd ? LiveArcState.Tell : LiveArcState.Quiet;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("own", _ownClock);
            w.WriteDouble("phase", Phase);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _ownClock = r.ReadDouble("own");
            Phase = r.ReadDouble("phase");
        }
    }
}
