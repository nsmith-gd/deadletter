using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Drives
{
    public enum WindCrankState { Idle, Winding }

    public enum WindCrankEvent
    {
        /// <summary>The wind: the chain runs (<c>Sound.chain(2.2)</c> + ratchet), 0.3 s into the act. Index = winds since the reset.</summary>
        Wind,
        /// <summary>The second ratchet click, 0.9 s into the act (L5374, L6093).</summary>
        Ratchet,
    }

    public sealed class WindCrankParams
    {
        public Station Station;
        /// <summary>The Crank clip, played where he stands (no turn into the set; L5320, L6021).</summary>
        public ActProfile Profile = new ActProfile("Crank");
        /// <summary>Seconds into the act at which the wind happens (<c>a.t &gt; 0.3</c>), the second ratchet clicks and the act ends.</summary>
        public double WindAt = 0.3, RatchetAt = 0.9, EndAt = 1.5;

        /// <summary>DL-14: the blinds' crank under the window, <c>ATT.crankX</c> 242.4; he stands 0.22 short of it; reach 0.36 (L292, L5291, L5298).</summary>
        public static WindCrankParams Dl14Crank() => new WindCrankParams
        {
            Station = new Station(standX: 242.4 - 0.22, reach: 0.36, face: +1, reachX: 242.4),
        };

        /// <summary>DL-14a: the dormitory crank, <c>ATT3.crankX</c> 258.7; stand 0.22 short; reach 0.34 (L5890, L5990, L6006).</summary>
        public static WindCrankParams Dl14aCrank() => new WindCrankParams
        {
            Station = new Station(standX: 258.7 - 0.22, reach: 0.34, face: +1, reachX: 258.7),
        };
    }

    /// <summary>
    /// A crank that gives one wind per act (§4.13g): the chain runs once, 0.3 s into the Crank act, and the act ends at
    /// 1.5 s (DL-14 L5364–L5376, DL-14a L6083–L6095). What the wind does is the driven mechanism's business
    /// (<see cref="PairedBlindDrive"/>). It always answers (the prototype never refuses a wind).
    /// Signals: <see cref="Position"/> = winds since the last reset (a count; the drive acts on each increase).
    /// </summary>
    public sealed class WindCrank : StationMechanism, IPositionSource
    {
        private readonly WindCrankParams _p;
        private ActInput _act;
        private bool _wound, _ratcheted;
        private int _winds;

        /// <summary>The view's spin while winding, rad/s (L5447).</summary>
        public const double SpinRate = 4;

        public WindCrank(MechanismId id, WindCrankParams p) : base(id, p.Station) { _p = p; }

        public WindCrankState State => (WindCrankState)StateCode;
        /// <summary>Winds since the last reset (<c>b.winds</c> is the drive's own count; this one only counts acts).</summary>
        public double Position => _winds;
        public int Winds => _winds;
        /// <summary>
        /// The crank's turn for its view, radians: it spins at 4 rad/s while an act winds it (<c>rotateZ(dt · 4)</c>, L5447).
        /// Presentation only: not saved, and kept across a reset (the art turns on from where it was).
        /// </summary>
        public double SpinRad { get; private set; }

        public override ActProfile Profile => _p.Profile;

        public override void Reset(in Checkpoint cp)
        {
            Init((int)WindCrankState.Idle);
            _winds = 0;
            _wound = _ratcheted = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => true;                    // L5291, L5990

        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return ActStep.DoneIf(f.Time > _p.EndAt + 1e-9);                                               // a.t > 1.5, L5375
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (_act.Active) SpinRad += ctx.Dt * SpinRate;
            if (!_act.Active)
            {
                Enter(ctx, (int)WindCrankState.Idle);
                return;
            }
            if (_act.Started) { _wound = _ratcheted = false; Enter(ctx, (int)WindCrankState.Winding); }
            if (!_wound && _act.Time > _p.WindAt + 1e-9)                                    // a.t > 0.3 && !a.done, L5366
            {
                _wound = true;
                _winds++;
                Emit(ctx, (int)WindCrankEvent.Wind, _winds);
            }
            if (!_ratcheted && _act.Time > _p.RatchetAt + 1e-9) { _ratcheted = true; Emit(ctx, (int)WindCrankEvent.Ratchet); }   // L5374
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("winds", _winds);
            w.WriteBool("wound", _wound);
            w.WriteBool("ratcheted", _ratcheted);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _winds = (int)r.ReadLong("winds");
            _wound = r.ReadBool("wound");
            _ratcheted = r.ReadBool("ratcheted");
            _act.Read(r);
        }
    }
}
