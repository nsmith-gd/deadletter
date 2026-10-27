using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Catches
{
    public enum CycleBrakeState { Free, Braked }

    public enum CycleBrakeEvent
    {
        /// <summary>Pulled with no cycle running: nothing to hold, it only clunks (L5344–L5348).</summary>
        Clunk,
    }

    public sealed class CycleBrakeParams
    {
        public Station Station;
        public ActProfile Profile = new ActProfile("Pull");   // L5319
        /// <summary>The pawl drops 0.35 s into the act (L5351, L6079).</summary>
        public double ToggleAfter = 0.35;
        /// <summary>The act ends after 1.0 s (L5361, L6080).</summary>
        public double DoneAfter = 1.0;
        /// <summary>Optional: the cycle's "running" signal (DL-13: the lesson is on). Unwired = always running (DL-14a).</summary>
        public MechanismId Running;
        public string BrakedAfter;

        /// <summary>DL-13: the lesson's brake. Stands 0.2 short of the pawl, answers within 0.4 of it (L5290, L5298).</summary>
        public static CycleBrakeParams Dl13Brake() => new CycleBrakeParams
        {
            Station = new Station(standX: 220.6 - 0.2, reach: 0.4, face: +1, reachX: 220.6),   // ATT.pawlX, L290
            Running = "dl13.lesson",
            BrakedAfter = "gallery13",                                                        // resetAtt, L5236
        };

        /// <summary>DL-14a: the night-light's brake (L5989, L6006, L6078–L6082).</summary>
        public static CycleBrakeParams Dl14aBrake() => new CycleBrakeParams
        {
            Station = new Station(standX: 252.3 - 0.2, reach: 0.3, face: +1, reachX: 252.3),   // ATT3.pawlX
            BrakedAfter = "corridor",                                                         // resetAtt3: braked = dark = past corridor, L5913–L5914
        };
    }

    /// <summary>
    /// A brake that freezes a cycle where it is (§4.13c, §4.13k): each pull toggles it. With the cycle not running it
    /// only clunks (DL-13). The cycle clock reads <see cref="Engaged"/> (= braked) and stops advancing.
    /// Whether the cycle is running is judged when the act starts; the prototype judged it when Use was pressed
    /// (<c>att:pawl</c> vs <c>att:pawlIdle</c>, L5290), a few steps earlier.
    /// </summary>
    public sealed class CycleBrake : StationMechanism, IEngageable
    {
        private readonly CycleBrakeParams _p;
        private IEngageable _running;
        private ActInput _act;
        private bool _idle, _done;

        public CycleBrake(MechanismId id, CycleBrakeParams p) : base(id, p.Station) { _p = p; }

        public CycleBrakeState State => (CycleBrakeState)StateCode;
        public bool Engaged => State == CycleBrakeState.Braked;

        public override ActProfile Profile => _p.Profile;

        public override void Link(MechanismLinker link) => _running = link.ReadAnyOrder<IEngageable>(_p.Running);

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(cp.Past(_p.BrakedAfter) ? CycleBrakeState.Braked : CycleBrakeState.Free));
            _idle = _done = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => true;

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return f.Time > _p.DoneAfter;
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active) return;
            if (_act.Started) { _idle = _running != null && !_running.Engaged; _done = false; }
            if (_done || !(_act.Time > _p.ToggleAfter)) return;
            _done = true;
            if (_idle) Emit(ctx, (int)CycleBrakeEvent.Clunk);                                          // L5346
            else Enter(ctx, (int)(Engaged ? CycleBrakeState.Free : CycleBrakeState.Braked));           // L5352, L6079
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("idle", _idle);
            w.WriteBool("done", _done);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _idle = r.ReadBool("idle");
            _done = r.ReadBool("done");
            _act.Read(r);
        }
    }
}
