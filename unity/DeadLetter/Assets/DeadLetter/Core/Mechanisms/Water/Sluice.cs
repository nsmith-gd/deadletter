using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Water
{
    public enum SluiceState { Shut, Open }

    public enum SluiceEvent
    {
        /// <summary>The gate drops or lifts: a pawl click and a clunk (L6194).</summary>
        Clunk,
    }

    public sealed class SluiceParams
    {
        public Station Station;
        /// <summary>Pulled like a lever (L6020).</summary>
        public ActProfile Profile = new ActProfile("Pull");
        /// <summary>The gate toggles 0.35 s into the act (L6194).</summary>
        public double ToggleAfter = 0.35;
        /// <summary>The act ends after 1.0 s (L6195).</summary>
        public double DoneAfter = 1.0;
        /// <summary>Every sluice starts open at every reset (<c>sluice: [1, 1, 1]</c>, L5923).</summary>
        public bool StartsOpen = true;

        /// <summary>
        /// DL-17: sluice <paramref name="i"/> (0 = A, 1 = B, 2 = C) at <c>ATT3.sluices[i]</c> (L5906). He stands 0.18 short of it and
        /// it answers within 0.24, from the floor (L5998, L6009).
        /// </summary>
        public static SluiceParams Dl17Sluice(int i)
        {
            double x = SluiceRigParams.Dl17SluiceX[i];
            return new SluiceParams { Station = new Station(standX: x - 0.18, reach: 0.24, face: +1, reachX: x) };
        }
    }

    /// <summary>
    /// One sluice gate of a water rig (§4.13i, the "Water" permanent rule): each pull toggles it open or shut. The rig
    /// reads <see cref="Engaged"/> (= open) every step, so a sluice changed mid-run changes the split at once
    /// (DL-17: L6009, L6193–L6196, L6249). Signals: <see cref="Engaged"/> = open.
    /// </summary>
    public sealed class Sluice : StationMechanism, IEngageable
    {
        private readonly SluiceParams _p;
        private ActInput _act;
        private bool _done;

        public Sluice(MechanismId id, SluiceParams p) : base(id, p.Station) { _p = p; }

        public SluiceState State => (SluiceState)StateCode;
        public bool Engaged => State == SluiceState.Open;
        public override ActProfile Profile => _p.Profile;

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(_p.StartsOpen ? SluiceState.Open : SluiceState.Shut));
            _done = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => true;

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return f.Time > _p.DoneAfter;                                                              // L6195
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active) return;
            if (_act.Started) _done = false;
            if (_done || !(_act.Time > _p.ToggleAfter)) return;
            _done = true;
            Enter(ctx, (int)(Engaged ? SluiceState.Shut : SluiceState.Open));                          // L6194
            Emit(ctx, (int)SluiceEvent.Clunk);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("done", _done);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _done = r.ReadBool("done");
            _act.Read(r);
        }
    }
}
