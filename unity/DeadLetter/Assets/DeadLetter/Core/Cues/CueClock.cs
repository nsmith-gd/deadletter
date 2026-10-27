using System;

namespace DeadLetter.Core.Cues
{
    /// <summary>
    /// A directed moment's time, in seconds from the cue's first sample as heard (index.html <c>Music.moment</c> L905–L910,
    /// <c>Music.momentTime</c> L915–L927, the start in <c>play</c> L876). The shot, the act and the lights read this, never
    /// the frame clock, so a frame stall or a decode delay cannot pull the camera off the music
    /// (docs/directed_moments.md, "One timeline").
    /// <list type="bullet">
    /// <item>It never runs backwards and freezes while the music clock is not running.</item>
    /// <item>With no music (no device, failed decode, a headless run) it runs on the simulation clock from the trigger.</item>
    /// <item>If the audio is suspended for more than 0.6 s before the cue started, or 2.0 s after, it falls back to the
    /// simulation clock from where it stood (L918).</item>
    /// </list>
    /// Deterministic given the same sequence of (music clock, sim time) readings.
    /// </summary>
    public sealed class CueClock
    {
        /// <summary>A moment's cue is scheduled this far ahead on the audio clock, and that is its zero (L876).</summary>
        public const double ScheduleLeadIn = 0.1;
        /// <summary>Unstarted / stalled limits before falling back to the sim clock, L918.</summary>
        public const double UnstartedFallback = 0.6, StalledFallback = 2.0;

        private readonly IMusicClock _music;
        private readonly double _prime;

        private double? _startAt;
        private double _t, _t0, _seenAt;

        /// <param name="music">The audio clock; null = always the sim-clock fallback.</param>
        /// <param name="prime">Decoder priming added to heard time (<c>PRIME = 0</c>, L797).</param>
        public CueClock(IMusicClock music, double prime = 0)
        {
            _music = music;
            _prime = prime;
        }

        /// <summary>The moment playing (<c>Music.momentName()</c>, L928), or null.</summary>
        public string MomentName { get; private set; }
        public bool Active => MomentName != null;
        /// <summary>True once the clock runs on the simulation clock.</summary>
        public bool Fallback { get; private set; }
        /// <summary>The audio-clock time of the cue's first sample, once scheduled.</summary>
        public double? StartAt => _startAt;

        /// <summary>
        /// <c>Music.moment(name)</c> (L907): a new moment from <paramref name="simTime"/>. Pass
        /// <paramref name="musicAvailable"/> false when there is no music (or in a headless/accelerated run, as the web
        /// sim does) to run on the sim clock.
        /// </summary>
        public void Begin(string name, double simTime, bool musicAvailable)
        {
            if (name == null) throw new ArgumentNullException(nameof(name));
            MomentName = name;
            _startAt = null;
            _t = 0;
            _t0 = simTime;
            _seenAt = simTime;
            Fallback = !musicAvailable || _music == null;
        }

        /// <summary>The cue's first sample is scheduled at <paramref name="audioTime"/> on the music clock (normally
        /// <c>Now + ScheduleLeadIn</c>, L876).</summary>
        public void Scheduled(double audioTime)
        {
            if (Active) _startAt = audioTime;
        }

        /// <summary>The cue could not start (decode failed, no clip): run on the sim clock from the trigger (L871, L919).</summary>
        public void MusicFailed()
        {
            if (Active) Fallback = true;
        }

        /// <summary><c>Music.endMoment()</c>, L929.</summary>
        public void End()
        {
            MomentName = null;
            _startAt = null;
            Fallback = false;
        }

        /// <summary>
        /// <c>Music.momentTime(name)</c>: seconds into the moment as heard, or null if <paramref name="name"/> is not the
        /// moment playing (null = any).
        /// </summary>
        public double? Time(string name, double simTime)
        {
            if (MomentName == null || (name != null && name != MomentName)) return null;
            bool running = _music != null && _music.Running;
            if (!Fallback && !running && simTime - _seenAt > (_startAt == null ? UnstartedFallback : StalledFallback))
            {
                Fallback = true;
                _t0 = simTime - _t;
            }
            if (Fallback) { _t = Math.Max(_t, simTime - _t0); return _t; }
            if (_startAt == null || !running) return _t;
            _seenAt = simTime;
            double heard = _music.Now - _music.OutputLatency;
            _t = Math.Max(_t, heard - _startAt.Value + _prime);
            return _t;
        }
    }
}
