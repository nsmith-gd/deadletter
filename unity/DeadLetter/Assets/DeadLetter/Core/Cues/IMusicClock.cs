namespace DeadLetter.Core.Cues
{
    /// <summary>
    /// The music's audio clock, as the cue clock reads it (port_architecture §4.18, §4.24). Runtime adapts
    /// <c>AudioSettings.dspTime</c> (<c>AudioDspMusicClock</c>); tests use a fake. All times in seconds.
    /// </summary>
    public interface IMusicClock
    {
        /// <summary>
        /// The audio clock now: the time base cues are scheduled on (<c>AudioSource.PlayScheduled</c>). Must never run
        /// backwards and must not advance while <see cref="Running"/> is false (paused, app hidden): the web build's
        /// <c>ctx.currentTime</c> (L922).
        /// </summary>
        double Now { get; }

        /// <summary>False while the audio is suspended (pause in a moment, hidden app, no device): <c>ctx.state</c>, L918.</summary>
        bool Running { get; }

        /// <summary>
        /// Seconds between a sample being scheduled and it reaching the speaker (mix buffer + device + a measured per-platform
        /// offset): the web build's <c>ctx.outputLatency || ctx.baseLatency</c>, L922. Subtracted so the camera follows the
        /// music <b>as heard</b>.
        /// </summary>
        double OutputLatency { get; }
    }
}
