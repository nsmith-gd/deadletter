using System;
using DeadLetter.Core.Cues;
using UnityEngine;

namespace DeadLetter.Runtime.Camera
{
    /// <summary>
    /// <see cref="IMusicClock"/> on Unity's audio DSP clock (port_architecture §4.24: "the moment clock is
    /// <c>AudioSettings.dspTime − start − outputLatency</c>").
    /// <list type="bullet">
    /// <item><b>Smoothing.</b> <c>dspTime</c> advances in whole mix buffers; between changes it is extrapolated on the
    /// realtime clock by at most one buffer (the web build's <c>getOutputTimestamp</c> path, index.html L923–L924), and it
    /// never runs backwards.</item>
    /// <item><b>Pause.</b> <see cref="SetPaused"/> freezes the clock and, on resume, removes the paused span, so a cue that
    /// was paused with <c>AudioSource.Pause</c> stays in step with the shot (L932–L936). Schedule cues with
    /// <see cref="ScheduleAhead"/> so the start is in both time bases.</item>
    /// <item><b>Latency.</b> mix buffer (<c>GetDSPBufferSize</c> × buffers ÷ <c>outputSampleRate</c>) plus a measured
    /// per-platform offset (Switch: to be measured on hardware).</item>
    /// </list>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class AudioDspMusicClock : MonoBehaviour, IMusicClock
    {
        [Serializable]
        public struct PlatformLatency
        {
            public RuntimePlatform platform;
            [Tooltip("Seconds added to the mix-buffer latency (device / OS output path). Measure with a clap test.")]
            public float offsetSeconds;
        }

        [Tooltip("Extra output latency per platform, on top of the mix buffer.")]
        [SerializeField] private PlatformLatency[] platformOffsets =
        {
            new PlatformLatency { platform = RuntimePlatform.WindowsPlayer, offsetSeconds = 0.0f },
            new PlatformLatency { platform = RuntimePlatform.OSXPlayer, offsetSeconds = 0.0f },
            new PlatformLatency { platform = RuntimePlatform.LinuxPlayer, offsetSeconds = 0.0f },
            new PlatformLatency { platform = RuntimePlatform.Switch, offsetSeconds = 0.0f },
        };
        [Tooltip("Used when the platform is not in the list (e.g. the Editor).")]
        [SerializeField] private float defaultOffsetSeconds;
        [Tooltip("Include the DSP mix buffer in the latency.")]
        [SerializeField] private bool includeMixBuffer = true;

        private double _lastDsp = double.NaN, _realAtDsp, _bufferSeconds, _latency;
        private double _pausedTotal, _pausedAtDsp, _lastNow;
        private bool _paused, _focusLost;

        public double Now
        {
            get
            {
                double now = Frozen ? _pausedAtDsp - _pausedTotal : SmoothedDsp() - _pausedTotal;
                if (now < _lastNow) now = _lastNow;
                _lastNow = now;
                return now;
            }
        }

        public bool Running => !Frozen && AudioSettings.outputSampleRate > 0;

        /// <summary>Paused by the game, or the app is in the background: the clock holds still either way.</summary>
        private bool Frozen => _paused || _focusLost;

        public double OutputLatency => _latency;

        /// <summary>Pause in a moment: the score stops where it is. Call through
        /// <see cref="DirectedMomentPlayer.SetPaused"/>, which also pauses the cue's AudioSource and the Timeline.</summary>
        public void SetPaused(bool paused)
        {
            if (paused == _paused) return;
            bool wasFrozen = Frozen;
            _paused = paused;
            OnFrozenChanged(wasFrozen);
        }

        // Game pause and backgrounding share one frozen span: entering it marks the DSP time, leaving it removes the
        // span from Now, so a cue paused or suspended mid-moment resumes in step with the shot (L932–L936, L939).
        private void SetFocusLost(bool lost)
        {
            if (lost == _focusLost) return;
            bool wasFrozen = Frozen;
            _focusLost = lost;
            OnFrozenChanged(wasFrozen);
        }

        private void OnFrozenChanged(bool wasFrozen)
        {
            if (Frozen == wasFrozen) return;
            if (Frozen) _pausedAtDsp = SmoothedDsp();
            else _pausedTotal += Math.Max(0, SmoothedDsp() - _pausedAtDsp);
        }

        /// <summary>
        /// A start <paramref name="leadIn"/> seconds ahead: <paramref name="dspTime"/> for <c>AudioSource.PlayScheduled</c>,
        /// the return value for <c>CueClock.Scheduled</c>.
        /// </summary>
        public double ScheduleAhead(double leadIn, out double dspTime)
        {
            dspTime = AudioSettings.dspTime + leadIn;
            return dspTime - _pausedTotal;
        }

        private void Awake() => RefreshLatency();

        private void OnEnable() => AudioSettings.OnAudioConfigurationChanged += OnAudioConfigChanged;
        private void OnDisable() => AudioSettings.OnAudioConfigurationChanged -= OnAudioConfigChanged;
        private void OnAudioConfigChanged(bool deviceWasChanged) => RefreshLatency();

        // A hidden / backgrounded app stops the frames; report the clock as not running so the cue clock freezes, and
        // drop the time spent in the background from Now, as SetPaused does (L939).
        private void OnApplicationPause(bool pause) => SetFocusLost(pause);

        public void RefreshLatency()
        {
            double offset = defaultOffsetSeconds;
            if (platformOffsets != null)
                for (int i = 0; i < platformOffsets.Length; i++)
                    if (platformOffsets[i].platform == Application.platform) { offset = platformOffsets[i].offsetSeconds; break; }
            AudioSettings.GetDSPBufferSize(out int bufferLength, out int numBuffers);
            int rate = AudioSettings.outputSampleRate;
            _bufferSeconds = rate > 0 ? (double)bufferLength / rate : 0;
            _latency = (includeMixBuffer && rate > 0 ? (double)bufferLength * Math.Max(1, numBuffers) / rate : 0) + offset;
        }

        private double SmoothedDsp()
        {
            double dsp = AudioSettings.dspTime;
            double real = Time.realtimeSinceStartupAsDouble;
            if (dsp != _lastDsp) { _lastDsp = dsp; _realAtDsp = real; return dsp; }
            return dsp + Math.Min(Math.Max(0, real - _realAtDsp), _bufferSeconds);
        }
    }
}
