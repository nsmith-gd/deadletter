using System;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Motor;
using UnityEngine;
using UnityEngine.Playables;

namespace DeadLetter.Runtime.Camera
{
    /// <summary>
    /// Runs the directed moments (port_architecture §4.18 <c>MomentPlayer</c>): Core's <see cref="MomentDirector"/> owns the
    /// timing; this starts the cue on the DSP clock, gates D-17's input, scrubs one Timeline per moment to the cue clock
    /// (<c>PlayableDirector</c> in Manual update, <c>time = cue time</c>, then <c>Evaluate</c>) and hands the moment's
    /// camera shot to <see cref="LaneCameraDriver"/>. Timelines carry lights, FX and animation beats; the camera pose
    /// itself stays in Core (<see cref="MomentShots"/>) so it is replay-testable.
    /// Scene rules (U-20–22) call <see cref="Trigger"/> at the prototype's triggers and set <see cref="ActReady"/>
    /// (kin: realise act idle; refuge: awe clip done; ringc: car gone) and <see cref="CarRise"/>.
    /// The pause card (U-17) must call <see cref="SetPaused"/> on open and close, or a moment keeps playing under it;
    /// checkpoint reload must call <see cref="ResetForReload"/>.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class DirectedMomentPlayer : MonoBehaviour
    {
        [Serializable]
        public sealed class Binding
        {
            [Tooltip("kin, refuge, ringc or window.")]
            public string moment;
            [Tooltip("Optional Timeline, scrubbed to the cue clock (Moment_kin, Moment_refuge, …).")]
            public PlayableDirector timeline;
            [Tooltip("The moment's cue. Without one (or with no clip) the moment runs on the sim clock.")]
            public AudioSource cue;
        }

        [SerializeField] private D17Controller player;
        [SerializeField] private AudioDspMusicClock musicClock;
        [Tooltip("Snapped on checkpoint reload (ResetForReload).")]
        [SerializeField] private LaneCameraDriver cameraDriver;
        [SerializeField] private Binding[] moments = new Binding[0];

        private MomentDirector _director;
        private Binding _active;
        private bool _paused;

        public MomentDirector Director => _director;

        /// <summary>The moment's act condition before control may return (see <c>MomentDirector.GateInput</c>).</summary>
        public Func<bool> ActReady { get; set; }

        /// <summary>DL-10's car travel <c>uo.d</c> for the car10 look (L3717).</summary>
        public double CarRise { get; set; }

        /// <summary>Voices, tannoys and distant clanks wait while this is true (L958).</summary>
        public bool VoicesHeld => _director != null && player != null && _director.VoicesHeld(player.SimTime);

        /// <summary>The ring C cold light's intensity now (L4619–L4620).</summary>
        public float RingCLight
        {
            get
            {
                if (_director?.Current == null || _director.Current.Name != PrologueMoments.RingC.Name || player == null) return 0f;
                return (float)MomentShots.RingCLight(_director.Time(player.SimTime), _director.ReturnedAt);
            }
        }

        private void Awake()
        {
            _director = new MomentDirector(musicClock);
        }

        private void OnEnable()
        {
            if (player != null) player.InputFilter = Gate;
        }

        private void OnDisable()
        {
            if (player != null && player.InputFilter == (Func<MotorInput, MotorInput>)Gate) player.InputFilter = null;
        }

        /// <summary><c>startMoment(name)</c> (L950): the cue from its top 0.1 s ahead on the DSP clock, no queue.</summary>
        public void Trigger(string momentName)
        {
            DirectedMoment m = PrologueMoments.Find(momentName);
            if (m == null) { Debug.LogWarning("Unknown directed moment " + momentName, this); return; }
            StopTimeline();
            _active = Find(momentName);
            AudioSource cue = _active?.cue;
            bool music = cue != null && cue.clip != null && musicClock != null && musicClock.Running;
            _director.Start(m, player != null ? player.SimTime : 0, music);
            if (music)
            {
                double clockTime = musicClock.ScheduleAhead(CueClock.ScheduleLeadIn, out double dsp);
                cue.time = 0f;
                cue.PlayScheduled(dsp);
                _director.Clock.Scheduled(clockTime);
            }
            if (_active?.timeline != null)
            {
                _active.timeline.timeUpdateMode = DirectorUpdateMode.Manual;
                _active.timeline.time = 0;
                _active.timeline.Play();
                _active.timeline.Evaluate();
            }
        }

        /// <summary>Checkpoint reset (L8017): no moment, no cut.</summary>
        public void ResetMoment()
        {
            StopTimeline();
            _director.End();
            _active = null;
        }

        /// <summary>
        /// Checkpoint reload: no moment, no cut, and the camera jumps to the respawn frame instead of easing out of the
        /// moment's shot (L8017, L8115). Subscribe this to <c>CheckpointService.Reloaded</c> (Core/Save, U-14) once that
        /// lands.
        /// </summary>
        public void ResetForReload()
        {
            ResetMoment();
            if (cameraDriver != null) cameraDriver.Snap();
        }

        /// <summary>
        /// Game pause (L932–L936): freezes the music clock (so the cue clock, shot and act hold), pauses the cue's
        /// AudioSource and the moment's Timeline; unpausing resumes all three in step. The pause card (U-17) must call
        /// this when it opens and closes. Safe to call with no moment playing.
        /// </summary>
        public void SetPaused(bool paused)
        {
            if (paused == _paused) return;
            _paused = paused;
            if (musicClock != null) musicClock.SetPaused(paused);
            AudioSource cue = _active?.cue;
            if (cue != null)
            {
                if (paused) cue.Pause();
                else cue.UnPause();
            }
            PlayableDirector timeline = _active?.timeline;
            if (timeline != null && _director.Current != null)
            {
                if (paused) timeline.Pause();
                else timeline.Resume();
            }
        }

        /// <summary>The moment's camera shot for D-17 at (x, y), or null (currentShot's moment branches, L3702–L3793).</summary>
        public ShotRequest? CurrentShot(double x, double y)
        {
            DirectedMoment m = _director.Current;
            if (m == null || player == null) return null;
            double sim = player.SimTime;
            if (m == PrologueMoments.Window)
            {
                // The ending's shot runs on the cue clock until he checks his label (L3744–L3751, L2113).
                double? wt = _director.Time(sim);
                return wt.HasValue && wt.Value < PrologueMoments.WindowLabelAt ? MomentShots.Window(x, y, wt.Value, wt) : (ShotRequest?)null;
            }
            double? t = _director.ShotTime(m.Name, sim);
            if (!t.HasValue) return null;
            if (m == PrologueMoments.Kin) return MomentShots.Kin(x, t.Value);
            if (m == PrologueMoments.Refuge) return MomentShots.Refuge(x, y, t.Value);
            if (m == PrologueMoments.RingC) return MomentShots.RingC(x, y, t.Value, CarRise);
            return null;
        }

        private MotorInput Gate(MotorInput raw)
        {
            bool ready = ActReady == null || ActReady();
            return _director.GateInput(raw, player.SimTime, ready);
        }

        private void LateUpdate()
        {
            if (_active?.timeline == null || _director.Current == null || player == null) return;
            double? t = _director.Time(player.SimTime);
            if (!t.HasValue) return;
            PlayableDirector d = _active.timeline;
            d.time = Math.Min(t.Value, d.duration);
            d.Evaluate();
        }

        private void StopTimeline()
        {
            if (_active?.timeline != null) _active.timeline.Stop();
        }

        private Binding Find(string name)
        {
            for (int i = 0; i < moments.Length; i++)
                if (moments[i] != null && moments[i].moment == name) return moments[i];
            return null;
        }
    }
}
