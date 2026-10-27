using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Catches
{
    public enum LatchState { Locked, Released }

    public enum LatchEvent
    {
        /// <summary>The lever creaks as it passes Pull f20 (L1873).</summary>
        Creak,
    }

    public sealed class LatchParams
    {
        /// <summary>Where he pulls it. Leave default (reach 0) for a latch nobody pulls (tripped by <see cref="Trigger"/> only).</summary>
        public Station Station;
        public ActProfile Profile = new ActProfile("Pull", crouch: true);
        /// <summary>Pull f31 releases it (L1874).</summary>
        public double ReleaseFrame = ClipTimings.PullEvents.Release;
        /// <summary>Pull f39 ends the act: the prototype then plays Flinch for 1.6 s (L1875–L1876).</summary>
        public double EndFrame = ClipTimings.PullEvents.Flinch;
        public double CreakFrame = 20;
        /// <summary>The Pull clip's frame rate (<c>FPS</c>, L268): after the act the lever runs on with the clip to its last key.</summary>
        public double ClipFps = 24;
        /// <summary>Lever angle once released (L8022).</summary>
        public double ReleasedLeverDeg = 72;
        /// <summary>Checkpoint from which it starts released (§4.28).</summary>
        public string ReleasedAfter;

        /// <summary>Optional: released when this source's Position reaches <see cref="Threshold"/> ...</summary>
        public MechanismId Trigger;
        public double Threshold = 1;
        /// <summary>... and more than Delay seconds have passed since it first did (it need not stay there; L5764).</summary>
        public double Delay;

        /// <summary>DL-01: crouch, pull the latch at the shutter's foot; releases the shutter (L1645–L1650, L1870–L1876).</summary>
        public static LatchParams Dl01Latch() => new LatchParams
        {
            Station = new Station(standX: 3.0, reach: 0.34, face: +1),   // PULL_ROOT_X L280, reach L1812
            ReleasedAfter = "shutter",                                    // CHECKPOINTS.shutter.released, L7977
        };
    }

    /// <summary>
    /// A one-way catch: Locked → Released (§4.13c, "Brakes and catches", full_game_plan §5). Released by the Pull act
    /// at <see cref="LatchParams.ReleaseFrame"/> (DL-01, L1870–L1876) or by a threshold on another mechanism
    /// (<c>dl17.latch</c> bed ≥ 0.95, L6258, now a <see cref="Water.FloatLatch"/>; <c>dl16.latch</c> 1.2 s after the rack is full, L5764).
    /// Signals: <see cref="Engaged"/> = released.
    /// </summary>
    public sealed class Latch : StationMechanism, IEngageable
    {
        /// <summary>Pull lever keys (frame, degrees), L1645–L1650.</summary>
        private static readonly double[] LeverKeyFrames = { 0, 12, 20, 24, 30, 33, 40 };
        private static readonly double[] LeverKeyDegs = { 0, 0, 12, 8, 22, 70, 72 };

        private readonly LatchParams _p;
        private IPositionSource _trigger;
        private ActInput _act;
        private double _armedFor = -1;
        private double _leverFrame = -1;

        public Latch(MechanismId id, LatchParams p) : base(id, p.Station) { _p = p; }

        public LatchState State => (LatchState)StateCode;
        public bool Engaged => State == LatchState.Released;
        /// <summary>The pull lever's angle, degrees (<c>game.leverAngle</c>).</summary>
        public double LeverDeg { get; private set; }

        public override ActProfile Profile => _p.Profile;

        public override void Link(MechanismLinker link) => _trigger = link.Read<IPositionSource>(_p.Trigger);

        public override void Reset(in Checkpoint cp)
        {
            bool released = cp.Past(_p.ReleasedAfter);
            Init((int)(released ? LatchState.Released : LatchState.Locked));
            LeverDeg = released ? _p.ReleasedLeverDeg : 0;
            _armedFor = -1;
            _leverFrame = -1;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => Station.Reach > 0 && State == LatchState.Locked;

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return ClipClock.Reached(f.Frame, _p.EndFrame);
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (_act.Active)
            {
                double f = _act.Frame;
                _leverFrame = f;
                LeverDeg = LeverAngleAt(f < 40 ? f : 40);                                       // L1872
                if (_act.PrevFrame <= _p.CreakFrame && f > _p.CreakFrame) Emit(ctx, (int)LatchEvent.Creak);   // L1873
                if (State == LatchState.Locked && ClipClock.Reached(f, _p.ReleaseFrame)) Enter(ctx, (int)LatchState.Released);   // L1874
            }
            else if (_leverFrame >= 0 && _leverFrame < 40)
            {
                // The act ends at Pull f39 (Flinch starts), but the prototype's latch branch still sets the lever from the
                // Pull clip's time while the Flinch plays (L1871–L1872), so it runs on to its last key, 72° at f40.
                _leverFrame += ctx.Dt * _p.ClipFps;
                LeverDeg = LeverAngleAt(_leverFrame < 40 ? _leverFrame : 40);
            }

            if (_trigger != null && State == LatchState.Locked)
            {
                if (_armedFor < 0) { if (_trigger.Position >= _p.Threshold) _armedFor = 0; }
                else _armedFor += ctx.Dt;
                if (_armedFor >= 0 && (_p.Delay <= 0 || _armedFor > _p.Delay)) Enter(ctx, (int)LatchState.Released);
            }
        }

        /// <summary><c>leverAngleAt</c>, L1645–L1650: smoothstep between keys.</summary>
        public static double LeverAngleAt(double f)
        {
            if (f <= 0) return 0;
            for (int i = 0; i < LeverKeyFrames.Length - 1; i++)
                if (f <= LeverKeyFrames[i + 1])
                    return LeverKeyDegs[i] + (LeverKeyDegs[i + 1] - LeverKeyDegs[i]) * Smooth.Step((f - LeverKeyFrames[i]) / (LeverKeyFrames[i + 1] - LeverKeyFrames[i]));
            return 72;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("lever", LeverDeg);
            w.WriteDouble("armedFor", _armedFor);
            w.WriteDouble("leverF", _leverFrame);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            LeverDeg = r.ReadDouble("lever");
            _armedFor = r.ReadDouble("armedFor");
            _leverFrame = r.ReadDouble("leverF");
            _act.Read(r);
        }
    }
}
