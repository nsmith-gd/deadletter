using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Water
{
    public enum SluiceValveState { Idle, Turning }

    public enum SluiceValveEvent
    {
        /// <summary>The handle comes round, 0.4 s into the act: the rig judges the run on this step (L6200).</summary>
        Turn,
    }

    public sealed class SluiceValveParams
    {
        public Station Station;
        /// <summary>Cranked (L6021).</summary>
        public ActProfile Profile = new ActProfile("Crank");
        /// <summary>The valve is turned 0.4 s into the act (L6200).</summary>
        public double TurnAfter = 0.4;
        /// <summary>The act ends after 1.5 s (L6207).</summary>
        public double DoneAfter = 1.5;

        /// <summary>
        /// DL-17: the rig's valve at <c>ATT3.valveX</c> 336.55 (L5906). He stands 0.2 short of it and it answers within 0.26, from
        /// the floor (L5999, L6007). The redesign dropped the key errand, so <c>valveLocked</c> is unreachable (L5999).
        /// </summary>
        public static SluiceValveParams Dl17Valve() => new SluiceValveParams
        {
            Station = new Station(standX: SluiceRigParams.Dl17ValveX - 0.2, reach: 0.26, face: +1, reachX: SluiceRigParams.Dl17ValveX),
        };
    }

    /// <summary>
    /// The valve that starts a water rig's run (§4.13i). It only turns: whether water flows is the rig's call, made on the
    /// step the handle comes round (DL-17, L6198–L6208). Signals: <see cref="Engaged"/> is true on that one step only.
    /// </summary>
    public sealed class SluiceValve : StationMechanism, IEngageable
    {
        private readonly SluiceValveParams _p;
        private ActInput _act;
        private bool _done, _turned;

        public SluiceValve(MechanismId id, SluiceValveParams p) : base(id, p.Station) { _p = p; }

        public SluiceValveState State => (SluiceValveState)StateCode;
        /// <summary>Turned this step (a one-step pulse the rig reads).</summary>
        public bool Engaged => _turned;
        public override ActProfile Profile => _p.Profile;

        public override void Reset(in Checkpoint cp)
        {
            Init((int)SluiceValveState.Idle);
            _done = _turned = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => true;

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return f.Time > _p.DoneAfter;                                                              // L6207
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            _turned = false;
            if (!_act.Active) { Enter(ctx, (int)SluiceValveState.Idle); return; }
            if (_act.Started) _done = false;
            Enter(ctx, (int)SluiceValveState.Turning);
            if (_done || !(_act.Time > _p.TurnAfter)) return;
            _done = _turned = true;                                                                    // L6200
            Emit(ctx, (int)SluiceValveEvent.Turn);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("done", _done);
            w.WriteBool("turned", _turned);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _done = r.ReadBool("done");
            _turned = r.ReadBool("turned");
            _act.Read(r);
        }
    }
}
