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
        /// <summary>
        /// DL-10: a new act carries on from the opening it was left at (<c>strokes: Math.round(uo.door · UO.strokes)</c>,
        /// L4318), so only the remaining strokes are needed. False (DL-01, which cannot be cancelled): each act counts from 0.
        /// </summary>
        public bool ResumeFromOpening;
        public string DoneAfter;

        /// <summary>DL-01: the exit door's crank, 5 strokes (L299, L1877–L1897).</summary>
        public static CrankParams Dl01Crank() => new CrankParams
        {
            // CRANK_X 9.62, reach 0.36 (L1813); he faces the crank from his side (x < CRANK_X ? 1 : −1, L1835).
            Station = new Station(standX: 9.62, reach: 0.36, face: 0, faceTowards: true),
            Strokes = 5,
            DoneAfter = "door",                       // CHECKPOINTS.door.door = 1, L7979
        };

        /// <summary>
        /// DL-10: the service door's crank, 4 strokes (<c>UO.strokes</c>, L3459, L4565–L4577). He stands at
        /// <c>UO.crankStand</c> = OFF5 + 72.45 (reach 0.25 on the deck, L4235) facing +x (L4318). Moving the stick after
        /// 0.5 s lets go; the door holds where left and the next act resumes from it.
        /// </summary>
        public static CrankParams Dl10ServiceCrank() => new CrankParams
        {
            Station = new Station(standX: 54 + 72.45, reach: 0.25, face: 1),   // OFF5 = 54, L274
            Strokes = 4,
            CancelAfter = 0.5, CancelMove = 0.3,                                // a.t > 0.5 && |move| > 0.3, L4575
            ResumeFromOpening = true,
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
        private int _actStrokes, _base;

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
            _actStrokes = _base = 0;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => Position < 1;   // L1813

        public override ActStep OnActFrame(in ActFrame f)
        {
            if (!_act.Active || f.Frame < _act.Frame)                            // the first frame of an act (as ActInput.Take)
                _base = _p.ResumeFromOpening ? Math.Min(_p.Strokes - 1, (int)Math.Floor(Position * _p.Strokes + 0.5)) : 0;   // L4318
            _act.Receive(f);
            if (StrokesAt(f.Frame) >= _p.Strokes) return ActStep.Done;           // L1889
            return ActStep.DoneIf(_p.CancelAfter >= 0 && f.Time > _p.CancelAfter && Math.Abs(f.Input.Move) > _p.CancelMove);   // L4575
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (!_act.Active)
            {
                if (State == CrankState.Cranking) Enter(ctx, (int)CrankState.Idle);
                return;
            }
            if (_act.Started) { _actStrokes = _base; Enter(ctx, (int)CrankState.Cranking); }

            int strokes = StrokesAt(_act.Frame);
            double local = Math.Max(0, _act.Frame - (strokes - _base) * _p.LoopFrames);   // actions.Crank.time · FPS (it loops)
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

        /// <summary>
        /// Strokes counted by the act at <paramref name="frame"/>, including those it resumed from. The loop wraps when
        /// the mixer's time reaches the clip's duration in seconds (three.js LoopRepeat); counting in frames, a wrap that
        /// lands on a step to within rounding is counted on that step (<see cref="WrapSlack"/>).
        /// </summary>
        private int StrokesAt(double frame) => _base + (int)Math.Floor((frame + WrapSlack) / _p.LoopFrames);

        /// <summary>Frames of slack for the loop wrap (seconds-vs-frames rounding), as before ClipClock became exact.</summary>
        private const double WrapSlack = 1e-6;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("open", Position);
            w.WriteDouble("wheel", WheelDeg);
            w.WriteLong("actStrokes", _actStrokes);
            w.WriteLong("base", _base);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("open");
            WheelDeg = r.ReadDouble("wheel");
            _actStrokes = (int)r.ReadLong("actStrokes");
            _base = (int)r.ReadLong("base");
            _act.Read(r);
        }
    }
}
