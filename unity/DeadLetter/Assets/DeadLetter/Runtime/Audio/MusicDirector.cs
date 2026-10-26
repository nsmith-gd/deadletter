using DeadLetter.Core.Audio;
using DeadLetter.Core.Cues;
using DeadLetter.Runtime.Camera;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// The score (port_architecture §4.24) on two AudioSource pairs, cue A/B and ambience A/B, scheduled on the DSP clock.
    /// Core's <see cref="MusicDirectorModel"/> makes every decision (which cue, the queue, handover bars, the wanted loop,
    /// the fades, the bus level); this binds its <see cref="MusicDirectorModel.Layers"/> to the four sources each frame:
    /// a new layer is started with <c>PlayScheduled</c> at its exact start on the music clock, its volume is its gain
    /// envelope × the bus level, and it is stopped when the model drops it. Times are <see cref="AudioDspMusicClock.Now"/>,
    /// the same clock the directed moments' <see cref="CueClock"/> reads, so a moment's camera and its cue cannot drift.
    /// Loops are clip-native (the importer trims the 2 s padding), so the ambience sources simply loop.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class MusicDirector : MonoBehaviour
    {
        [SerializeField] private SfxBank bank;
        [SerializeField] private AudioDspMusicClock musicClock;
        [Tooltip("Master > Music (with the limiter).")]
        [SerializeField] private AudioMixerGroup musicGroup;
        [Tooltip("How far ahead handovers and queued cues are scheduled (s). More than a frame; small enough that a late " +
                 "ambience change still lands.")]
        [Range(0.02f, 0.5f)]
        [SerializeField] private float scheduleHorizon = 0.1f;

        private readonly MusicDirectorModel _model = new MusicDirectorModel();
        private readonly AudioSource[] _cue = new AudioSource[2], _amb = new AudioSource[2];
        private readonly int[] _cueLayer = { -1, -1 }, _ambLayer = { -1, -1 };
        private bool _sourcesPaused;

        public MusicDirectorModel Model => _model;

        /// <summary>The music clock now (the model's time base).</summary>
        public double Now => musicClock != null ? musicClock.Now : AudioSettings.dspTime;

        private void Awake()
        {
            for (int i = 0; i < 2; i++)
            {
                _cue[i] = NewSource("Cue " + (char)('A' + i));
                _amb[i] = NewSource("Ambience " + (char)('A' + i));
            }
            if (bank != null)
                foreach (MusicTrack t in MusicCatalog.All)
                {
                    AudioClip c = bank.MusicClip(t.Key);
                    if (c != null) _model.SetLength(t.Key, c.length);
                }
        }

        // ---- The prototype's Music API, on the music clock -----------------------------------------------------------

        public void Play(string cue, float fadeIn = (float)MusicDirectorModel.DefaultFadeIn)
        {
            _model.Play(cue, Now, fadeIn);
            if (Clip(cue) == null) _model.CueFailed(cue, Now);
        }

        public void Queue(string cue) => _model.Queue(cue, Now);
        public void Stop(float seconds = (float)MusicDirectorModel.StopFade) => _model.Stop(Now, seconds);
        public void Ambience(string loop, float fadeIn = 4f, float fadeOut = 4f, float scale = 1f) => _model.Ambience(loop, Now, fadeIn, fadeOut, scale);
        public void Bed(bool on) => _model.Bed(on, Now);
        public void Duck(bool on) => _model.Duck(on, Now);
        public void SetEnabled(bool on) => _model.SetEnabled(on, Now);
        public string Playing => _model.Playing;

        /// <summary>
        /// <c>Music.setPaused</c>: the score steps down to 0.45; in a directed moment it stops where it is, with the music
        /// clock, so the shot and the score resume together (L932–L936).
        /// </summary>
        public void SetPaused(bool on)
        {
            if (on && _model.InMoment) PauseSources(true);
            _model.SetPaused(on, Now);
            if (!on && _sourcesPaused) PauseSources(false);
        }

        /// <summary>True if <paramref name="momentCue"/> has a clip to play (else the moment runs on the sim clock).</summary>
        public bool CanPlay(string momentCue) => Clip(momentCue) != null && musicClock != null && musicClock.Running;

        /// <summary>
        /// <c>Music.moment(name)</c>: the cue from its top, <see cref="CueClock.ScheduleLeadIn"/> ahead, at full level.
        /// Returns its start on the music clock for <see cref="CueClock.Scheduled"/>.
        /// </summary>
        public double StartMoment(string momentCue)
        {
            double start = _model.Moment(momentCue, Now);
            Sync(Now);
            return start;
        }

        /// <summary>The moment's cue could not play: the ambience comes back (pair with <see cref="CueClock.MusicFailed"/>).</summary>
        public void MomentFailed(string momentCue) => _model.CueFailed(momentCue, Now);

        // ---- Frame -------------------------------------------------------------------------------------------------------

        private void Update()
        {
            if (_sourcesPaused) return;
            double now = Now;
            _model.Update(now, now + scheduleHorizon);
            Sync(now);
        }

        private void Sync(double now)
        {
            for (int slot = 0; slot < 2; slot++)
            {
                Bind(_cue[slot], ref _cueLayer[slot], Find(MusicLayerKind.Cue, slot), now);
                Bind(_amb[slot], ref _ambLayer[slot], Find(MusicLayerKind.Ambience, slot), now);
            }
        }

        private void Bind(AudioSource source, ref int boundId, MusicLayer layer, double now)
        {
            if (layer == null)
            {
                if (boundId >= 0) { source.Stop(); boundId = -1; }
                return;
            }
            if (layer.Id != boundId)
            {
                source.Stop();
                boundId = layer.Id;
                AudioClip clip = Clip(layer.Key);
                source.clip = clip;
                source.loop = layer.Loop;
                if (clip != null)
                {
                    source.timeSamples = 0;
                    source.PlayScheduled(ToDsp(layer.StartAt));
                }
                else if (layer == _model.CurrentCue)
                {
                    // A cue the model started by itself (a queue, a handover) with no clip in the bank: as a failed
                    // decode in the web build, the ambience comes back (L871).
                    Debug.LogWarning("[Audio] No clip for music key '" + layer.Key + "'. Run Dead Letter → Audio → Import Audio.", this);
                    _model.CueFailed(layer.Key, now);
                }
            }
            double bus = _model.BusLevel(now);
            source.volume = Mathf.Clamp01((float)(layer.Gain.ValueAt(now) * bus));
        }

        /// <summary>A music-clock time as <c>AudioSettings.dspTime</c> (the clock excludes paused spans).</summary>
        private double ToDsp(double clockTime)
        {
            if (musicClock == null) return clockTime;
            double clockNow = musicClock.ScheduleAhead(0, out double dspNow);
            return clockTime + (dspNow - clockNow);
        }

        private MusicLayer Find(MusicLayerKind kind, int slot)
        {
            var layers = _model.Layers;
            for (int i = 0; i < layers.Count; i++)
                if (layers[i].Kind == kind && layers[i].Slot == slot) return layers[i];
            return null;
        }

        private void PauseSources(bool pause)
        {
            _sourcesPaused = pause;
            for (int i = 0; i < 2; i++)
            {
                if (pause) { _cue[i].Pause(); _amb[i].Pause(); }
                else { _cue[i].UnPause(); _amb[i].UnPause(); }
            }
            if (musicClock != null) musicClock.SetPaused(pause);
        }

        private AudioClip Clip(string key) => bank != null ? bank.MusicClip(key) : null;

        private AudioSource NewSource(string name)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            AudioSource s = go.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.spatialBlend = 0f;
            s.outputAudioMixerGroup = musicGroup;
            s.volume = 0f;
            return s;
        }
    }
}
