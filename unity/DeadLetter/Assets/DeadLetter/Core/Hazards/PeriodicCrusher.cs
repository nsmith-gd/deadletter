using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Hazards
{
    /// <summary>Where the ram is in its cycle (<c>pressFace</c>, L7310–L7316).</summary>
    public enum CrusherState
    {
        /// <summary>Up, at rest (from <see cref="PeriodicCrusherParams.RiseEnd"/> to the end of the period).</summary>
        Up,
        /// <summary>Still up, the lamp blinking: the tell (0 to <see cref="PeriodicCrusherParams.TellEnd"/>).</summary>
        Tell,
        /// <summary>Coming down (to <see cref="PeriodicCrusherParams.DropEnd"/>).</summary>
        Falling,
        /// <summary>Down on the bed (to <see cref="PeriodicCrusherParams.DownEnd"/>).</summary>
        Down,
        /// <summary>Going back up (to <see cref="PeriodicCrusherParams.RiseEnd"/>).</summary>
        Rising,
    }

    public enum CrusherEvent
    {
        /// <summary>
        /// The ram reaches the bed (<c>t &gt;= DropEnd &amp;&amp; t − dt &lt; DropEnd</c>) while he is within
        /// <see cref="PeriodicCrusherParams.HearRange"/>: a thud, a clank and a shake. Value = the shake (0.15 · max(0.2, 1 − d / 6), L7350).
        /// </summary>
        Slam,
        /// <summary>He is under the ram while its face is below <see cref="PeriodicCrusherParams.Lethal"/> and his feet are below
        /// <see cref="PeriodicCrusherParams.BelowY"/> (L7351). Emitted on every such step; the scene's <see cref="DeathRule"/> kills him once.</summary>
        Crushed,
    }

    public sealed class PeriodicCrusherParams
    {
        /// <summary>The lethal span under the ram (open: <c>x &gt; x0 &amp;&amp; x &lt; x1</c>).</summary>
        public double X0, X1;
        /// <summary>The ram's face at rest and down, metres above the floor.</summary>
        public double Rest, Down;
        /// <summary>The cycle, seconds; its phase is the game clock modulo this (<c>game.clock % period</c>).</summary>
        public double Period;
        /// <summary>Phase boundaries: the tell ends, the ram is down, it starts to rise, it is back up (L7311–L7315).</summary>
        public double TellEnd = 0.5, DropEnd = 0.62, DownEnd = 0.97, RiseEnd = 1.57;
        /// <summary>The drop's and the rise's durations, as the prototype writes them (<c>/ 0.12</c>, <c>/ 0.6</c>): 1.57 − 0.97 is not 0.6 in doubles.</summary>
        public double DropTime = 0.12, RiseTime = 0.6;
        /// <summary>Below this face height the ram kills (<c>face &lt; lethal</c>).</summary>
        public double Lethal;
        /// <summary>He is only crushed with his feet below this (<c>game.y &lt; 0.3</c>).</summary>
        public double BelowY = 0.3;
        /// <summary>The slam is heard (and shakes) within <see cref="HearRange"/> of <see cref="HearX"/>; the shake is <see cref="SlamShake"/> · max(<see cref="MinLoud"/>, 1 − d / range).</summary>
        public double HearX, HearRange = 6, SlamShake = 0.15, MinLoud = 0.2;
        /// <summary>What a crush is.</summary>
        public DeathKind Kills = DeathKind.Crush;

        /// <summary>
        /// DL-02's franking press (<c>PRESS2</c>, L7309; <c>pressFace</c> L7310–L7316; L7343–L7351): under 13.62–14.28,
        /// face 0.98 at rest, 0.055 down, a 2.6 s cycle, lethal below 0.74, heard within 6 m of 13.95.
        /// </summary>
        public static PeriodicCrusherParams Dl02Press() => new PeriodicCrusherParams
        {
            X0 = 13.62, X1 = 14.28, Rest = 0.98, Down = 0.055, Period = 2.6, Lethal = 0.74,   // PRESS2, L7309
            BelowY = 0.3,                                                                       // L7351
            HearX = 13.95, HearRange = 6, SlamShake = 0.15, MinLoud = 0.2,                       // L7349–L7350
        };
    }

    /// <summary>
    /// A ram that stamps on a fixed cycle (§4.14; DL-02's franking press): its face is a pure function of the game
    /// clock's phase (<c>pressFace(game.clock % period)</c>, L7310–L7316, L7345), so it keeps its rhythm through deaths and
    /// respawns exactly as the prototype's does. The scene binds the game clock (<see cref="BindClock"/>); unbound (tests),
    /// it runs on its own clock from 0. Each step it reports the slam and whether D-17 is under it while it kills
    /// (<see cref="CrusherEvent.Crushed"/>); killing him is the scene's (<see cref="DeathRule"/>).
    /// Signals: <see cref="Position"/> = the face's height, metres; <see cref="Engaged"/> = lethal now.
    /// Presentation: <see cref="Lamp"/>, <see cref="WheelRad"/>.
    /// </summary>
    public sealed class PeriodicCrusher : Mechanism, IPositionSource, IEngageable
    {
        private readonly PeriodicCrusherParams _p;
        private Func<double> _clock;
        private double _ownClock;

        public PeriodicCrusher(MechanismId id, PeriodicCrusherParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (!(p.Period > 0)) throw new ArgumentException("A crusher needs a period.");
            Face = p.Rest;
        }

        public PeriodicCrusherParams Params => _p;
        public CrusherState State => (CrusherState)StateCode;
        /// <summary>The ram's face, metres above the floor (<c>pressFace(t)</c>).</summary>
        public double Face { get; private set; }
        /// <summary>Seconds into the cycle (<c>game.clock % period</c>).</summary>
        public double Phase { get; private set; }
        public double Position => Face;
        public bool Engaged => Face < _p.Lethal;
        /// <summary>The lamp's glow: a blink during the tell (steady when calm), lit while it is down (L7347).</summary>
        public double Lamp(bool calm) => Phase < _p.TellEnd && !calm ? (Math.Sin(Phase * 25) > -0.2 ? 6 : 0.4) : Phase < _p.DownEnd ? 2 : 0;
        /// <summary>The flywheel: one turn per stroke, radians about the lane's z (L7348).</summary>
        public double WheelRad => -(Time() / _p.Period) * Math.PI * 2;

        /// <summary>The game clock this crusher keeps time with (the scene's <c>game.clock</c>). Null: its own clock.</summary>
        public void BindClock(Func<double> seconds) => _clock = seconds;

        /// <summary><c>pressFace</c>, L7310–L7316 (<c>THREE.MathUtils.lerp</c> = (1 − t)·a + t·b).</summary>
        public double FaceAt(double t)
        {
            var p = _p;
            if (t < p.TellEnd) return p.Rest;
            if (t < p.DropEnd) return Lerp(p.Rest, p.Down, Smooth.Step((t - p.TellEnd) / p.DropTime));
            if (t < p.DownEnd) return p.Down;
            if (t < p.RiseEnd) return Lerp(p.Down, p.Rest, Smooth.Step((t - p.DownEnd) / p.RiseTime));
            return p.Rest;
        }

        /// <summary>He would be crushed at (x, y) now (L7351, without the scene's "alive").</summary>
        public bool Crushes(double x, double y) => x > _p.X0 && x < _p.X1 && Face < _p.Lethal && y < _p.BelowY;

        /// <summary>Nothing to derive: the ram follows the clock, which a respawn does not turn back.</summary>
        public override void Reset(in Checkpoint cp)
        {
            Evaluate();
            Init((int)StateAt(Phase));
        }

        public override void Step(in StepContext ctx)
        {
            if (_clock == null) _ownClock += ctx.Dt;
            Evaluate();
            Enter(ctx, (int)StateAt(Phase));
            var pl = ctx.Player;
            double t = Phase, d = Math.Abs(pl.X - _p.HearX);
            if (d < _p.HearRange && t >= _p.DropEnd && t - ctx.Dt < _p.DropEnd)                                   // L7349–L7350
                Emit(ctx, (int)CrusherEvent.Slam, 0, _p.SlamShake * Math.Max(_p.MinLoud, 1 - d / _p.HearRange));
            if (Crushes(pl.X, pl.Y)) Emit(ctx, (int)CrusherEvent.Crushed, (int)_p.Kills, pl.X);                    // L7351
        }

        private double Time() => _clock != null ? _clock() : _ownClock;

        private void Evaluate()
        {
            Phase = Time() % _p.Period;                                                                             // L7345 (JS % = C# %, fmod)
            Face = FaceAt(Phase);
        }

        private CrusherState StateAt(double t)
            => t < _p.TellEnd ? CrusherState.Tell : t < _p.DropEnd ? CrusherState.Falling : t < _p.DownEnd ? CrusherState.Down
             : t < _p.RiseEnd ? CrusherState.Rising : CrusherState.Up;

        private static double Lerp(double a, double b, double t) => (1 - t) * a + t * b;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("own", _ownClock);
            w.WriteDouble("face", Face);
            w.WriteDouble("phase", Phase);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _ownClock = r.ReadDouble("own");
            Face = r.ReadDouble("face");
            Phase = r.ReadDouble("phase");
        }
    }
}
