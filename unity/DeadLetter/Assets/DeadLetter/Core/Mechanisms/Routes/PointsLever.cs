using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Routes
{
    public enum PointsLeverState
    {
        /// <summary>Stop lever: the belt is stopped. Points: set to the chute.</summary>
        Off,
        /// <summary>Stop lever: the belt runs. Points: set to the exit (the service ramp).</summary>
        On,
    }

    public enum PointsLeverEvent
    {
        /// <summary>LeverPull f22: it toggled (klaxon or belt stop; the points' clack). Index = 1 if now On (L2930–L2934).</summary>
        Thrown,
        /// <summary>LeverStuck f12 and f21: the interlock clunks (<c>game.triedPoints</c> on the second; L2918–L2919). Index = 0, 1.</summary>
        Clunk,
        /// <summary>The points went to the exit: the route shot (<c>routeShotAt</c>, L2933).</summary>
        RouteShot,
        /// <summary>The act ended with the points on the exit, not stuck: the Proud quirk (L2907).</summary>
        Proud,
        /// <summary>The <see cref="PointsLeverParams.StartWith"/> signal came on: it switched On by itself (<c>startBelt</c>: klaxon, L2822).</summary>
        AutoStart,
    }

    public sealed class PointsLeverParams
    {
        public Station Station;
        public ActProfile PullProfile = new ActProfile("LeverPull", turnIntoSet: true);
        public ActProfile StuckProfile = new ActProfile("LeverStuck", turnIntoSet: true);
        public double ThrowFrame = ClipTimings.LeverEvents.Throw, OutFrame = ClipTimings.LeverEvents.Out, StuckOutFrame = ClipTimings.LeverEvents.StuckDone;
        /// <summary>Lever angle, degrees, at rest Off and On (the view eases toward it at rate 8, L2832–L2834).</summary>
        public double OffDeg, OnDeg;
        /// <summary>Optional <see cref="IEngageable"/>: while it is engaged when the act starts, the lever is stuck (the points while the belt runs, L2910).</summary>
        public MechanismId Lock;
        /// <summary>Optional <see cref="IEngageable"/>: the lever answers only while it is engaged, and switches On when it comes on (the scanner done, L2814, L2867).</summary>
        public MechanismId StartWith;
        /// <summary>Emit <see cref="PointsLeverEvent.Proud"/> and <see cref="PointsLeverEvent.RouteShot"/> (the points).</summary>
        public bool IsPoints;
        /// <summary>On from <see cref="OnAfter"/> until (not including) <see cref="OnUntil"/> (§4.28).</summary>
        public string OnAfter, OnUntil;

        /// <summary>DL-06: the stop lever, <c>STOP_LEVER_X</c> 62.5; Off = belt stopped (LEVER_NEAR 6°), On = running (LEVER_AWAY −18°); the belt runs from <c>scanned</c> (L2457–L2458, L8032–L8034).</summary>
        public static PointsLeverParams Dl06StopLever() => new PointsLeverParams
        {
            // reach 0.38 (L2867); steps in to LEVER_Z + 0.26 = 0.11 (three) = −0.11 (Unity, §0.2), L2901
            Station = new Station(standX: 33 + 29.5, reach: 0.38, face: +1, standZ: -0.11),
            OffDeg = 6, OnDeg = -18,
            StartWith = "dl06.scanner",
            OnAfter = "scanned",                                       // game.belt.running = !!c.scanned, L8032
        };

        /// <summary>DL-06: the points lever, <c>POINTS_LEVER_X</c> 63.3; Off = chute (−18°), On = exit (6°); stuck while the belt runs (L2457–L2458, L2910).</summary>
        public static PointsLeverParams Dl06Points() => new PointsLeverParams
        {
            Station = new Station(standX: 33 + 30.3, reach: 0.38, face: +1, standZ: -0.11),
            OffDeg = -18, OnDeg = 6,
            Lock = "dl06.stopLever", StartWith = "dl06.scanner", IsPoints = true,
            OnAfter = "landing", OnUntil = "school",                   // game.route = c.upper ? 'exit' : 'chute', L8032 (upper: landing..forwarded)
        };
    }

    /// <summary>
    /// A two-way lever on the return line (§4.13h): the stop lever toggles the belt, the points lever the route at the
    /// junction; the points only move while the belt is stopped (the interlock), otherwise the lever rattles
    /// (LeverStuck) and nothing changes (L2895–L2937). Stuck is judged when the act starts (L2910).
    /// Signals: <see cref="Engaged"/> = On (belt running / route to the exit).
    /// </summary>
    public sealed class PointsLever : StationMechanism, IEngageable
    {
        private readonly PointsLeverParams _p;
        private IEngageable _lock, _start;
        private ActInput _act;
        private bool _stuck, _clipStuck, _thrown, _ended, _startWas;
        private double _from;

        public PointsLever(MechanismId id, PointsLeverParams p) : base(id, p.Station) { _p = p; }

        public PointsLeverState State => (PointsLeverState)StateCode;
        public bool Engaged => State == PointsLeverState.On;
        /// <summary>The lever's angle, degrees (<c>game.leverHold.angle</c> in an act, else the rest angle).</summary>
        public double LeverDeg { get; private set; }
        public bool Locked => _lock != null && _lock.Engaged;

        /// <summary>Asked when Use starts and again at the end of step-in, which decides the clip (<c>stuck = points && belt running</c>, L2910).</summary>
        public override ActProfile Profile => Locked ? _p.StuckProfile : _p.PullProfile;

        public override void Link(MechanismLinker link)
        {
            _lock = link.Read<IEngageable>(_p.Lock);
            _start = link.Read<IEngageable>(_p.StartWith);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool on = cp.Past(_p.OnAfter) && !cp.Past(_p.OnUntil);
            Init((int)(on ? PointsLeverState.On : PointsLeverState.Off));
            LeverDeg = RestDeg;
            _stuck = _clipStuck = _thrown = _ended = false;
            _from = LeverDeg;
            _startWas = _start != null && _start.Engaged;
            _act.Clear();
        }

        private double RestDeg => Engaged ? _p.OnDeg : _p.OffDeg;

        protected override bool CanUse(in InteractionQuery q) => _start == null || _start.Engaged;   // scan.phase === 'done', L2867

        /// <summary>The clip the motor chose at the end of step-in says which it is (LeverStuck or LeverPull, L2910–L2912).</summary>
        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            _clipStuck = f.Clip != null ? f.Clip == _p.StuckProfile.Clip : Locked;
            return ActStep.DoneIf(ClipClock.Reached(f.Frame, _clipStuck ? _p.StuckOutFrame : _p.OutFrame));
        }

        public override void Step(in StepContext ctx)
        {
            if (_start != null)
            {
                bool now = _start.Engaged;
                if (now && !_startWas && State == PointsLeverState.Off && !_p.IsPoints) { Enter(ctx, (int)PointsLeverState.On); Emit(ctx, (int)PointsLeverEvent.AutoStart); }   // startBelt, L2815
                _startWas = now;
            }

            _act.Take();
            if (!_act.Active) { LeverDeg = RestDeg; return; }
            if (_act.Started) { _stuck = _clipStuck; _thrown = _ended = false; _from = RestDeg; }    // L2910–L2911
            double f = _act.Frame, prev = _act.PrevFrame;
            if (_stuck)
            {
                double jig = (f > 10 && f < 17 ? Math.Sin((f - 10) * 0.9) : 0) + (f > 19 && f < 26 ? 1.4 * Math.Sin((f - 19) * 0.9) : 0);
                LeverDeg = _from + 2.5 * jig;                                                      // L2916–L2917
                if (prev <= 12 && f > 12) Emit(ctx, (int)PointsLeverEvent.Clunk, 0);              // L2918
                if (prev <= 21 && f > 21) Emit(ctx, (int)PointsLeverEvent.Clunk, 1);              // L2919
                return;
            }
            double to = _from > (_p.OnDeg + _p.OffDeg) / 2 ? Math.Min(_p.OnDeg, _p.OffDeg) : Math.Max(_p.OnDeg, _p.OffDeg);   // L2911
            LeverDeg = _from + (to - _from) * Smooth.Step((f - 10) / 12);                          // L2923–L2924
            if (!_thrown && ClipClock.Reached(f, _p.ThrowFrame))                                  // L2925–L2934
            {
                _thrown = true;
                bool on = !Engaged;
                Enter(ctx, (int)(on ? PointsLeverState.On : PointsLeverState.Off));
                Emit(ctx, (int)PointsLeverEvent.Thrown, on ? 1 : 0);
                if (_p.IsPoints && on) Emit(ctx, (int)PointsLeverEvent.RouteShot);
            }
            if (!_ended && ClipClock.Reached(f, _p.OutFrame))
            {
                _ended = true;
                if (_p.IsPoints && Engaged) Emit(ctx, (int)PointsLeverEvent.Proud);               // L2907
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("lever", LeverDeg);
            w.WriteDouble("from", _from);
            w.WriteBool("stuck", _stuck); w.WriteBool("clipStuck", _clipStuck); w.WriteBool("thrown", _thrown); w.WriteBool("ended", _ended);
            w.WriteBool("startWas", _startWas);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            LeverDeg = r.ReadDouble("lever");
            _from = r.ReadDouble("from");
            _stuck = r.ReadBool("stuck"); _clipStuck = r.ReadBool("clipStuck"); _thrown = r.ReadBool("thrown"); _ended = r.ReadBool("ended");
            _startWas = r.ReadBool("startWas");
            _act.Read(r);
        }
    }
}
