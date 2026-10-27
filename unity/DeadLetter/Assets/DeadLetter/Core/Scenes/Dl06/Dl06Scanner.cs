using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl06
{
    /// <summary>The scanner's phase (<c>game.scan.phase</c>, L2775–L2815).</summary>
    public enum Dl06ScanPhase
    {
        /// <summary>Waiting for him under the arch (screen READY).</summary>
        Idle,
        /// <summary>He stands to attention while the bar sweeps him, his lamps answer, it reads 114 and refuses it (0 → 4.0 s).</summary>
        Scan,
        /// <summary>The pit: he walks to the rail by himself, slowly, until the label check at 17.2 s.</summary>
        Reveal,
        /// <summary>He checks his label (<c>CheckLabel</c>, done at f83).</summary>
        Check,
        /// <summary>Done: the belt has started, the levers and the carriers answer.</summary>
        Done,
    }

    public enum Dl06ScanEvent
    {
        /// <summary>The bar starts down (<c>Sound.scanSweep</c>, <c>SCAN.SWEEP</c> 0.5 s, L2783).</summary>
        Sweep,
        /// <summary>His chest lamp i answers the scanner's (<c>SCAN.ANSWER</c> + 0.2 i, L2784–L2789). Index = i.</summary>
        Answer,
        /// <summary>The screen reads RING C 114 (<c>Sound.chirp</c>, <c>SCAN.READ</c> 2.8 s, L2791).</summary>
        Read,
        /// <summary>RING C SEALED: the buzzer, the <c>dead</c> cue, the <c>tan_scanner</c> voice 0.35 s later (<c>SCAN.REJECT</c> 3.2 s, L2792).</summary>
        Reject,
        /// <summary>He perks up during the label check (<c>Sound.chirp</c>, CheckLabel f56, L2811).</summary>
        Perk,
    }

    /// <summary>
    /// DL-06's sorting scanner (<c>dl06.scanner</c>; <c>updateScan</c>, L2774–L2818, <c>SCAN</c> L2465): its sequence's
    /// clock and phase. Under the arch (<c>x ≥ SCANNER_X − 0.06</c>, on the floor of region 3, standing, hands empty, in no
    /// act) it starts; 4.0 s later the reveal; from 17.2 s, once he stands free, the label check; at CheckLabel's f83 it is
    /// done (<c>startBelt</c>: the stop lever reads this, <see cref="Mechanisms.Routes.PointsLeverParams.StartWith"/>). The
    /// acts that hold him meanwhile and the checkpoint are the scene's rules (<see cref="ReturnToSender06"/>), which read
    /// the transitions; the hatch's carrier at 3.6 s is <see cref="Dl06Hatch"/>'s.
    /// Signals: <see cref="Engaged"/> = done.
    /// </summary>
    public sealed class Dl06Scanner : Mechanism, IEngageable
    {
        private bool _sweep, _read, _rejected, _perked;
        private int _answered;

        public Dl06Scanner(MechanismId id) : base(id) { }

        public Dl06ScanPhase Phase => (Dl06ScanPhase)StateCode;
        public bool Engaged => Phase == Dl06ScanPhase.Done;
        /// <summary>Seconds since the scan started (<c>sc.t</c>); 30 when the world is built past it (L8031).</summary>
        public double T { get; private set; }
        /// <summary>The CheckLabel clip's time during the check (the mixer's: 0 on the step it starts).</summary>
        public double CheckT { get; private set; }
        /// <summary>The refusal has happened (<c>sc.rejected</c>): the floor arrows light toward the route (L2817).</summary>
        public bool Rejected => _rejected;

        /// <summary><c>game.region === 3 &amp;&amp; !game.upper</c> (L2777): the scene's (default: always).</summary>
        public Func<bool> OnSortingFloor = () => true;
        /// <summary><c>game.mantle</c> (L2807): the scene's (default: never).</summary>
        public Func<bool> Climbing = () => false;

        public override void Reset(in Checkpoint cp)
        {
            bool done = cp.Past(Dl06Scene.ScannedCheckpoint);                                       // scan: { phase: 'done', t: 30, rejected }, L8031
            Init((int)(done ? Dl06ScanPhase.Done : Dl06ScanPhase.Idle));
            T = done ? 30 : 0;
            CheckT = 0;
            _sweep = _read = _perked = done;
            _rejected = done;
            _answered = done ? 3 : 0;
        }

        public override void Step(in StepContext ctx)
        {
            var p = ctx.Player;
            if (Phase == Dl06ScanPhase.Idle)
            {
                if (OnSortingFloor() && p.X >= Dl06Scene.ScannerX - Dl06Scene.ScanReach && p.Grounded && !p.Busy && !p.Holding)   // L2777
                {
                    T = 0;
                    Enter(ctx, (int)Dl06ScanPhase.Scan);                                            // L2778
                }
                return;
            }
            T += ctx.Dt;                                                                             // L2782
            double t = T;
            switch (Phase)
            {
                case Dl06ScanPhase.Scan:
                    if (!_sweep && t > Dl06Scene.ScanSweep) { _sweep = true; Emit(ctx, (int)Dl06ScanEvent.Sweep); }   // L2789
                    for (int i = _answered; i < 3; i++)                                             // L2790–L2794
                    {
                        if (!(t > Dl06Scene.ScanAnswer + i * 0.2 && t < Dl06Scene.ScanAnswer + i * 0.2 + 0.35)) break;
                        _answered = i + 1;
                        Emit(ctx, (int)Dl06ScanEvent.Answer, i);
                    }
                    if (t >= Dl06Scene.ScanRead && !_read) { _read = true; Emit(ctx, (int)Dl06ScanEvent.Read); }      // L2796
                    if (t >= Dl06Scene.ScanReject && !_rejected) { _rejected = true; Emit(ctx, (int)Dl06ScanEvent.Reject); }   // L2797
                    if (t >= Dl06Scene.ScanReveal) Enter(ctx, (int)Dl06ScanPhase.Reveal);                 // L2799
                    break;
                case Dl06ScanPhase.Reveal:
                    if (t >= Dl06Scene.ScanCheck && p.Grounded && !p.Busy && !Climbing())                   // L2802
                    {
                        CheckT = 0;
                        Enter(ctx, (int)Dl06ScanPhase.Check);
                    }
                    break;
                case Dl06ScanPhase.Check:
                    CheckT += ctx.Dt;                                                                       // actions.CheckLabel.time (the mixer ran after the step it started)
                    double f = CheckT * Dl06Scene.Fps;
                    if (f >= Dl06Scene.CheckPerkFrame && !_perked) { _perked = true; Emit(ctx, (int)Dl06ScanEvent.Perk); }   // L2809
                    if (f >= Dl06Scene.CheckDoneFrame) Enter(ctx, (int)Dl06ScanPhase.Done);                  // L2810–L2813
                    break;
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("t", T); w.WriteDouble("checkT", CheckT);
            w.WriteBool("sweep", _sweep); w.WriteBool("read", _read); w.WriteBool("rejected", _rejected); w.WriteBool("perked", _perked);
            w.WriteLong("answered", _answered);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            T = r.ReadDouble("t"); CheckT = r.ReadDouble("checkT");
            _sweep = r.ReadBool("sweep"); _read = r.ReadBool("read"); _rejected = r.ReadBool("rejected"); _perked = r.ReadBool("perked");
            _answered = (int)r.ReadLong("answered");
        }
    }

    /// <summary>
    /// The dispatch hatch (<c>dl06.hatch</c>): at the scan's HATCH beat (3.6 s) a carrier rises to take the refused parcel,
    /// if none is on the line (<c>if (t &gt;= SCAN.HATCH &amp;&amp; !refs.carriers.length) spawnCarrier()</c>, L2798). The
    /// line reads it as its <see cref="Mechanisms.Routes.CarrierLineParams.Hatch"/>. Signals: <see cref="Engaged"/> = the
    /// scanner is in its scan phase and past HATCH.
    /// </summary>
    public sealed class Dl06Hatch : Mechanism, IEngageable
    {
        private readonly MechanismId _scannerId;
        private Dl06Scanner _scanner;

        public Dl06Hatch(MechanismId id, MechanismId scanner) : base(id) { _scannerId = scanner; }

        public bool Engaged => _scanner.Phase == Dl06ScanPhase.Scan && _scanner.T >= Dl06Scene.ScanHatch;

        public override void Link(MechanismLinker link)
            => _scanner = link.Read<Dl06Scanner>(_scannerId) ?? throw new InvalidOperationException(Id + " needs the scanner.");

        public override void Reset(in Checkpoint cp) => Init(0);
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }
}
