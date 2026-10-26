using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Actuators
{
    public enum CrankState { Idle, Cranking, Done }

    public enum CrankEvent
    {
        /// <summary>A stroke finished (ratchet, rumble, shake; L1888). Index = strokes so far in this act.</summary>
        Stroke,
    }

    public sealed class CrankParams
    {
        public Station Station;
        public ActProfile Profile = new ActProfile("Crank", turnIntoSet: true);
        /// <summary>Strokes from shut to open; each opens 1/Strokes, eased over its first <see cref="RiseFrames"/>.</summary>
        public int Strokes = 5;
        public double StrokeDeg = 60;
        /// <summary>Crank loop length, frames (<c>LOOP_FRAMES.Crank</c>, L315).</summary>
        public double LoopFrames = 24;
        public double RiseFrames = 12;
        /// <summary>DL-10: moving the stick past <see cref="CancelMove"/> after CancelAfter seconds stops cranking; it holds where left. &lt; 0 = never.</summary>
        public double CancelAfter = -1, CancelMove = 0.3;
        public string DoneAfter;

        /// <summary>DL-01: the exit door's crank, 5 strokes (L299, L1877–L1897).</summary>
        public static CrankParams Dl01Crank() => new CrankParams
        {
            // CRANK_X 9.62, reach 0.36 (L1813). The prototype faces him toward the crank from his side (L1835);
            // IStation.Face cannot depend on his side, so 0 keeps his facing (he turns into the set either way).
            Station = new Station(standX: 9.62, reach: 0.36, face: 0),
            Strokes = 5,
            DoneAfter = "door",                       // CHECKPOINTS.door.door = 1, L7979
        };
    }

    /// <summary>
    /// A hand crank that winds something open over n strokes (§4.13d; DL-01 door L1877–L1897, DL-10 service door
    /// L4565–L4577). Each stroke of the Crank loop adds 1/n, eased over its first 12 frames; the opening never goes
    /// back (<c>max</c>). n strokes in one act finish it (<see cref="CrankState.Done"/>; DL-01 then sets the
    /// <c>door</c> checkpoint and plays <c>threshold</c>, L1889). Signals: <see cref="Position"/> = opening, 0..1.
    /// </summary>
    public sealed class CrankActuator : StationMechanism, IPositionSource
    {
        private readonly CrankParams _p;
        private ActInput _act;
        private int _actStrokes;

        public CrankActuator(MechanismId id, CrankParams p) : base(id, p.Station) { _p = p; }

        public CrankState State => (CrankState)StateCode;
        /// <summary>Opening, 0..1 (<c>game.doorOpen</c>).</summary>
        public double Position { get; private set; }
        /// <summary>Wheel angle, degrees (<c>game.wheelAngle</c>).</summary>
        public double WheelDeg { get; private set; }

        public override ActProfile Profile => _p.Profile;

        public override void Reset(in Checkpoint cp)
        {
            bool done = cp.Past(_p.DoneAfter);
            Init((int)(done ? CrankState.Done : CrankState.Idle));
            Position = done ? 1 : 0;
            WheelDeg = done ? _p.Strokes * _p.StrokeDeg : 0;                      // L8024
            _actStrokes = 0;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => Position < 1;   // L1813

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            if (StrokesAt(f.Frame) >= _p.Strokes) return true;                   // L1889
            return _p.CancelAfter >= 0 && f.Time > _p.CancelAfter && Math.Abs(f.Input.Move) > _p.CancelMove;   // L4575
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active)
            {
                if (State == CrankState.Cranking) Enter(ctx, (int)CrankState.Idle);
                return;
            }
            if (_act.Started) { _actStrokes = 0; Enter(ctx, (int)CrankState.Cranking); }

            int strokes = StrokesAt(_act.Frame);
            double local = Math.Max(0, _act.Frame - strokes * _p.LoopFrames);    // actions.Crank.time · FPS (it loops)
            double s = local <= _p.RiseFrames ? Smooth.Step(local / _p.RiseFrames) : 1;
            // The opening uses the act's stroke count before this step's wrap, as the prototype did (L1885–L1886).
            Position = Math.Max(Position, Math.Min(1, (_actStrokes + s) / _p.Strokes));
            // The wheel uses the count after it: the prototype's wheel snapped back one stroke for one step per wrap.
            WheelDeg = strokes * _p.StrokeDeg + _p.StrokeDeg * s;

            if (strokes > _actStrokes)                                                                // f < a.lastF, L1887
            {
                _actStrokes = strokes;
                Emit(ctx, (int)CrankEvent.Stroke, strokes);
                if (strokes >= _p.Strokes) { Position = 1; WheelDeg = _p.Strokes * _p.StrokeDeg; Enter(ctx, (int)CrankState.Done); }   // L1889
            }
        }

        private int StrokesAt(double frame) => (int)Math.Floor((frame + ClipClock.Epsilon) / _p.LoopFrames);

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("open", Position);
            w.WriteDouble("wheel", WheelDeg);
            w.WriteLong("actStrokes", _actStrokes);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("open");
            WheelDeg = r.ReadDouble("wheel");
            _actStrokes = (int)r.ReadLong("actStrokes");
            _act.Read(r);
        }
    }
}
