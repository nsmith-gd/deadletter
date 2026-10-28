using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// He plays a few clips where he stands, raising a cue in each (DL-18's chain, clock and sketch, DL-19's pot: no state changes). Its
    /// phase is the beat's clip or look, which the view plays (<see cref="ChapterSim.SceneActPhase"/>); the motor stands
    /// meanwhile. Not cancellable: each lasts a few seconds.
    /// </summary>
    public sealed class BeatAct : SceneAct
    {
        /// <summary>One clip: its phase, how long it plays, and the cue it raises <c>CueAt</c> seconds in (none: <see cref="CueId.None"/>).</summary>
        public readonly struct Beat
        {
            public readonly ActId Phase;
            public readonly double Seconds, CueAt;
            public readonly CueId Cue;

            public Beat(ActId phase, double seconds, CueId cue, double cueAt)
            {
                if (!(seconds > 0)) throw new ArgumentOutOfRangeException(nameof(seconds));
                Phase = phase; Seconds = seconds; Cue = cue; CueAt = cueAt;
            }
        }

        private readonly Beat[] _beats;
        private int _i;
        private double _t;
        private bool _cued;

        public BeatAct(ActId kind, Beat[] beats) : base(kind, beats != null && beats.Length > 0 ? beats[0].Phase : throw new ArgumentException("No beats.", nameof(beats)))
        {
            _beats = beats;
        }

        /// <summary>Which beat is playing (0 first).</summary>
        public int Index => _i;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            _t += dt;
            var b = _beats[_i];
            if (!_cued && !b.Cue.IsNone && _t >= b.CueAt - 1e-9) { _cued = true; sim.Cue(b.Cue); }
            if (_t < b.Seconds - 1e-9) return true;
            if (++_i >= _beats.Length) return false;
            _t = 0;
            _cued = false;
            Phase = _beats[_i].Phase;
            return true;
        }
    }
}
