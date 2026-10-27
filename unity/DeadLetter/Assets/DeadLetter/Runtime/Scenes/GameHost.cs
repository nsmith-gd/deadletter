using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Simulation;
using DeadLetter.Core.Streaming;
using DeadLetter.Runtime.Audio;
using DeadLetter.Runtime.Camera;
using DeadLetter.Runtime.Platform;
using DeadLetter.Runtime.Save;
using DeadLetter.Runtime.Settings;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// The one boot owner (port_architecture §3, §7): lives in <c>DL_Persistent</c>, owns the chapter's Core
    /// <see cref="ChapterSim"/> (one world for the whole chapter) and ticks it at a fixed 60 Hz from Update, and feeds the thin
    /// adapters around it. It decides nothing: every outcome is the sim's (§2 "Rules").
    /// <list type="number">
    /// <item><b>Boot</b> (Awake): the platform's save store (<see cref="PlatformSaveStore"/>), the sim over it, and
    /// <see cref="CheckpointTrigger.Service"/> set at once, so <see cref="SettingsStore"/> applies the slot's options (calm mode
    /// above all: photosensitivity) before the first rendered frame. D-17 (<see cref="D17Controller"/>, hosted), the camera
    /// rig (stepped here, rendered by <see cref="LaneCameraDriver"/>) and the mechanism views are attached.</item>
    /// <item><b>Entry</b> (Start): Continue from the slot (or a new game, or <see cref="startAt"/> for testing). The scene the
    /// checkpoint belongs to (<see cref="ChapterSim.SceneOf"/>) and its neighbours are loaded behind the fade first, then
    /// the sim places him (<see cref="ChapterSim.Continue"/>, <see cref="ChapterSim.NewGame"/>).</item>
    /// <item><b>Each frame</b>: the scene views stream (<see cref="StreamingPlanner"/> from
    /// <see cref="ChapterSim.DistanceToSeam"/>); then each step: D-17's input → <see cref="ChapterSim.Step"/> → the camera rig →
    /// D-17's transform endpoints → the step's cues (music, voices, sounds, moments, shakes) → the mechanism views' samples.
    /// A respawn into a scene that is not loaded holds the step behind the fade until it is.</item>
    /// <item><b>Pause</b> (<see cref="PauseGate"/>, through <see cref="PlatformServicesHost"/>): no steps, the moment player
    /// paused; play time stops.</item>
    /// </list>
    /// Scenes are views only: a view scene unloading or loading never touches the sim.
    /// </summary>
    [DisallowMultipleComponent]
    // After D17Controller's Update (it latches this frame's presses), so a press is stepped the frame it happens. Its Awake
    // runs after D-17's and the camera driver's (they accept being attached after their own Awake) and after SettingsStore's
    // (-900), which picks the service up through CheckpointTrigger.ServiceChanged; all of this precedes the first frame.
    [DefaultExecutionOrder(10)]
    public sealed class GameHost : MonoBehaviour, ID17HostPose
    {
        [Header("Chapter")]
        [Tooltip("The chapter this host simulates (ChapterScenes.Ids).")]
        [SerializeField] private string chapterId = ChapterDefs.PrologueId;
        [Tooltip("Continue from the save slot when it holds a checkpoint of this chapter; otherwise a new game.")]
        [SerializeField] private bool continueFromSave = true;
        [Tooltip("A new game starts on the opening's last step (the wake's label beat). The opening itself (§3.1 #3) is not ported yet.")]
        [SerializeField] private bool startFromOpening = true;
        [Tooltip("Testing: begin at this checkpoint (e.g. \"bay\") instead of continuing; the slot's flags are kept, nothing is written.")]
        [SerializeField] private string startAt = "";
        [Tooltip("Metres from a seam at which the next scene loads. 0 = the platform's (StreamingRadii: larger on Switch).")]
        [SerializeField] private float streamingRadius;

        [Header("Presentation")]
        [SerializeField] private D17Controller player;
        [SerializeField] private LaneCameraDriver cameraDriver;
        [SerializeField] private DirectedMomentPlayer moments;
        [SerializeField] private MusicDirector score;
        [SerializeField] private VoicePlayer voices;
        [SerializeField] private AudioWorld audioWorld;
        [SerializeField] private ScreenFade fade;
        [Tooltip("Empty = PlatformServicesHost.Instance.")]
        [SerializeField] private PlatformServicesHost platformHost;

        private enum Phase { Off, Entering, Playing, Holding }
        private enum Entry { NewGame, Continue, Begin }

        private readonly List<int> _required = new List<int>(8), _load = new List<int>(4), _unload = new List<int>(4);
        private readonly FramingSignalTable _signals = new FramingSignalTable();
        private readonly CueRoutes _routes = new CueRoutes();
        private readonly HashSet<int> _unknownCues = new HashSet<int>();
        private ISaveStore _store;
        private FixedTick _tick;
        private PauseGate _pause;
        private Phase _phase;
        private Entry _entry;
        private string _entryCheckpoint;
        private int _currentIndex = -1;
        private bool _paused, _reloaded;

        public static GameHost Instance { get; private set; }

        /// <summary>The chapter's Core world (null before Awake or when the chapter is unknown).</summary>
        public ChapterSim Sim { get; private set; }
        public ChapterPresenter Presenter { get; private set; }
        public StreamingPlanner Planner { get; private set; }
        public SceneStreamer Streamer { get; private set; }
        /// <summary>The lane camera's rig, stepped here once per Core step (§3.1 #10) and rendered by the driver.</summary>
        public CameraRig Rig { get; private set; }
        /// <summary>In play: placed, not waiting for a load (pause aside).</summary>
        public bool InPlay => _phase == Phase.Playing;
        public bool Paused => _paused;

        /// <summary>Every cue of every step, after the host has dispatched it (subtitles, debug, scene-specific views).</summary>
        public event Action<Cue> CueRaised;
        /// <summary>The scene that holds him changed (<see cref="ChapterSim.SceneChanged"/>), after the views were committed.</summary>
        public event Action<SceneDef, SceneDef, ExitDir> SceneCommitted;
        /// <summary>He walked past the chapter's last scene: the next chapter's turn (its loading card is the caller's).</summary>
        public event Action ChapterExited;

        // ---- ID17HostPose: D-17 where the sim says (a scene act may own his pose) -----------------------------------------
        double ID17HostPose.X => Sim.X;
        double ID17HostPose.Y => Sim.Y;
        double ID17HostPose.Z => Sim.Z;
        double ID17HostPose.Yaw => Sim.Yaw;

        private double Aspect => cameraDriver != null ? cameraDriver.Aspect : 16.0 / 9.0;

        // ---- Boot ------------------------------------------------------------------------------------------------------
        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("GameHost: a second host was found; disabling it.", this);
                enabled = false;
                return;
            }
            ChapterDef def = ChapterScenes.Create(chapterId);
            if (def == null)
            {
                Debug.LogError("GameHost: no chapter '" + chapterId + "' (known: " + string.Join(", ", ChapterScenes.Ids) + ").", this);
                enabled = false;
                return;
            }
            Instance = this;

            IPlatformServices services = PlatformServices.Current;   // PlatformServicesHost (order −1000) has initialised it
            _store = PlatformSaveStore.Create(services);
            Sim = new ChapterSim(def, null, _store);
            Sim.Checkpoints.MinSecondsBetweenWrites = PlatformSaveStore.MinSecondsBetweenWrites(services.Kind);
            // The service read the slot's options in its constructor: setting it now makes SettingsStore apply them (calm mode,
            // volumes, bindings) before anything renders.
            CheckpointTrigger.Service = Sim.Checkpoints;

            Presenter = new ChapterPresenter(Sim);
            Planner = new StreamingPlanner(def, streamingRadius > 0 ? streamingRadius : StreamingRadii.For(services.Kind));
            var ids = new string[Planner.Count];
            var paths = new string[Planner.Count];
            for (int i = 0; i < ids.Length; i++)
            {
                ids[i] = Planner[i].Id;
                paths[i] = ChapterScenes.ScenePath(def.Id, Planner[i].Id);
            }
            Streamer = new SceneStreamer(ids, paths);
            _tick = new FixedTick(ChapterSim.StepSeconds, 4);

            Rig = new CameraRig(CameraConfig.Prototype, PrologueFraming.Build());
            if (cameraDriver != null) cameraDriver.BindRig(Rig);
            if (player != null) player.AttachToHost(Sim.Motor, Sim.Resolver, () => (float)_tick.Alpha, () => Sim.Clock, this);
            if (player != null && SettingsStore.Loaded) Sim.Motor.AutoRun = SettingsStore.Current.AutoRun;

            Sim.SceneChanged += OnSceneChanged;
            Sim.Checkpoints.Reloaded += OnReloaded;
            MechanismViewRegistry.Attach(ById(Sim), ById(ReferenceSim(def.Id)), () => SettingsStore.Calm);

            PlatformServicesHost ph = platformHost != null ? platformHost : PlatformServicesHost.Instance;
            if (ph != null)
            {
                _pause = ph.Pause;
                _pause.Changed += OnPauseChanged;
                ph.InPlay = () => _phase == Phase.Playing;
            }
            else Debug.LogWarning("GameHost: no PlatformServicesHost; pause and platform overlays will not stop the game.", this);

            if (fade != null) fade.FadeOut(instant: true);
        }

        private void Start()
        {
            if (Sim == null) return;
            if (!string.IsNullOrEmpty(startAt))
            {
                if (Sim.CanContinueAt(startAt)) { Enter(Entry.Begin, startAt); return; }
                Debug.LogWarning("GameHost: startAt '" + startAt + "' is not a checkpoint of " + chapterId + "'s scenes; continuing as usual.", this);
            }
            if (continueFromSave && _store.TryLoad(Sim.Checkpoints.Slot, out SaveModel m) && m != null && !m.OptionsOnly && Sim.CanContinueAt(m.Checkpoint))
                Enter(Entry.Continue, m.Checkpoint);
            else Enter(Entry.NewGame, Sim.Def.Checkpoints.Order[0]);
        }

        private void OnDestroy()
        {
            if (Instance != this) return;
            if (Sim != null)
            {
                Sim.Checkpoints.Flush();
                Sim.SceneChanged -= OnSceneChanged;
                Sim.Checkpoints.Reloaded -= OnReloaded;
                if (CheckpointTrigger.Service == Sim.Checkpoints) CheckpointTrigger.Service = null;
            }
            if (_pause != null) _pause.Changed -= OnPauseChanged;
            MechanismViewRegistry.Detach();
            Instance = null;
        }

        private void OnApplicationPause(bool paused) { if (paused) Sim?.Checkpoints.Flush(); }
        private void OnApplicationQuit() => Sim?.Checkpoints.Flush();

        /// <summary>A sim at the chapter's first placed checkpoint: the state the art is authored in (the views' rest values).</summary>
        private static ChapterSim ReferenceSim(string chapterId)
        {
            var reference = new ChapterSim(ChapterScenes.Create(chapterId));
            foreach (CheckpointDef cp in reference.Def.Checkpoints.All)
                if (reference.CanContinueAt(cp.Name)) { reference.Begin(cp.Name); break; }
            return reference;
        }

        private static Dictionary<string, IMechanism> ById(ChapterSim sim)
        {
            var map = new Dictionary<string, IMechanism>(StringComparer.Ordinal);
            foreach (SceneDef s in sim.Def.Scenes)
                foreach (IMechanism m in sim.MechanismsOf(s)) map[m.Id.Value] = m;
            return map;
        }

        // ---- Entry: load behind the fade, then place him ----------------------------------------------------------------
        private void Enter(Entry entry, string checkpoint)
        {
            _entry = entry;
            _entryCheckpoint = checkpoint;
            int scene = Planner.IndexOf(Sim.SceneOf(checkpoint));
            Planner.Placement(scene, _required);
            for (int i = 0; i < _required.Count; i++) Streamer.Load(_required[i]);
            Application.backgroundLoadingPriority = ThreadPriority.High;
            if (fade != null) fade.FadeOut();
            _phase = Phase.Entering;
            Debug.Log("GameHost: " + entry + " at '" + checkpoint + "' (" + (scene >= 0 ? Planner[scene].Id : "no scene") + "); loading " + Streamer.Describe() + ".", this);
        }

        private void PerformEntry()
        {
            switch (_entry)
            {
                case Entry.Continue:
                    if (!Sim.Continue())
                    {
                        Debug.LogWarning("GameHost: the slot could not be continued in " + chapterId + "; starting a new game.", this);
                        Enter(Entry.NewGame, Sim.Def.Checkpoints.Order[0]);
                        return;
                    }
                    break;
                case Entry.NewGame:
                    Sim.NewGame(startFromOpening);
                    break;
                case Entry.Begin:
                    Sim.Begin(_entryCheckpoint);
                    break;
            }
            _phase = Phase.Playing;
            _tick.Reset();
            Application.backgroundLoadingPriority = ThreadPriority.Low;
            AfterPlacement(fromOpening: _entry == Entry.NewGame && startFromOpening);
        }

        /// <summary>
        /// The next step respawns him in scene <paramref name="scene"/>, which is not loaded: hold the sim (it is behind the death
        /// cut) and load the checkpoint's slot and its neighbours behind the fade; the step runs when they are in.
        /// </summary>
        private void Hold(int scene)
        {
            Planner.Placement(scene, _required);
            for (int i = 0; i < _required.Count; i++) Streamer.Load(_required[i]);
            Application.backgroundLoadingPriority = ThreadPriority.High;
            if (fade != null) fade.FadeOut();
            _phase = Phase.Holding;
            Debug.Log("GameHost: respawn into " + Planner[scene].Id + " waits for " + Streamer.Describe() + ".", this);
        }

        private void OnReloaded(Checkpoint _) => _reloaded = true;

        /// <summary>He was placed (a new game, continue, begin or respawn): nothing interpolates across it.</summary>
        private void AfterPlacement(bool fromOpening)
        {
            _reloaded = false;
            _currentIndex = Planner.IndexOf(Sim.Current);
            if (player != null) player.SnapToMotor();
            Presenter.UpdateSignals(_signals);
            CameraRigInput input = Presenter.CameraInput(Aspect, _signals);
            Rig.SnapToFrame(input);
            Rig.Step(input, 0);
            if (cameraDriver != null) cameraDriver.Snap();
            MechanismViewRegistry.Sample();
            MechanismViewRegistry.Snap();
            if (score != null) MusicCues.CheckpointStart(score.Model, score.Now, fromOpening);
            CommitViews();
            if (fade != null) fade.FadeIn();
        }

        // ---- The frame ---------------------------------------------------------------------------------------------------
        private void Update()
        {
            if (Sim == null) return;
            Streamer.Poll();
            switch (_phase)
            {
                case Phase.Entering:
                    if (Streamer.AllReady(_required) && (fade == null || fade.IsBlack)) PerformEntry();
                    return;
                case Phase.Holding:
                    if (!Streamer.AllReady(_required) || (fade != null && !fade.IsBlack)) return;
                    _phase = Phase.Playing;                                  // the held step runs now and respawns him
                    _tick.Reset();
                    Application.backgroundLoadingPriority = ThreadPriority.Low;
                    break;
                case Phase.Playing:
                    break;
                default:
                    return;
            }

            if (_paused)
            {
                Sim.Checkpoints.Update(Time.unscaledDeltaTime, playing: false);
                return;
            }

            StreamAhead();
            int steps = _tick.Advance(Time.deltaTime);
            for (int i = 0; i < steps; i++)
            {
                SceneDef respawnIn = Presenter.PendingRespawnScene();
                if (respawnIn != null)
                {
                    int r = Planner.IndexOf(respawnIn);
                    if (r >= 0 && !Streamer.IsReady(r)) { Hold(r); break; }
                }
                StepOnce();
            }
            Sim.Checkpoints.Update(Time.unscaledDeltaTime, playing: true);
            PresentFrame();
        }

        private void LateUpdate()
        {
            if (Sim == null || _phase == Phase.Off || _phase == Phase.Entering) return;
            MechanismViewRegistry.Apply(player != null ? player.RenderAlpha : Mathf.Clamp01((float)_tick.Alpha));
        }

        /// <summary>One Core step and what reads it (§3.1: #2 input in, #4–#9 Core, #10–#11 presentation, #12 input consumed).</summary>
        private void StepOnce()
        {
            MotorInput input = player != null ? player.TakeInput() : default;
            Sim.Step(input);
            Presenter.UpdateSignals(_signals);
            Rig.Step(Presenter.CameraInput(Aspect, _signals), ChapterSim.StepSeconds);   // before D-17's Stepped: the driver reads the rig there
            if (player != null) player.OnHostStepped(ChapterSim.StepSeconds);
            Dispatch(Sim.Cues);
            MechanismViewRegistry.Sample();
            if (_reloaded) AfterPlacement(fromOpening: false);              // a respawn this step
        }

        /// <summary>Per frame, after the steps: the audio world, the ambience, and D-17's clip while a scene act holds him.</summary>
        private void PresentFrame()
        {
            if (audioWorld != null) audioWorld.region = Sim.Region;
            if (score != null) AmbienceRules.Apply(score.Model, Presenter.Ambience(), score.Now);
            if (player != null)
            {
                string clip = Presenter.ActClip(out double seconds);
                if (clip != player.OverrideClip)
                {
                    player.OverrideClipTime = double.IsNaN(seconds) ? 0 : seconds;
                    player.OverrideClip = clip;
                }
            }
        }

        // ---- Streaming ---------------------------------------------------------------------------------------------------
        private void StreamAhead()
        {
            if (_currentIndex < 0) return;
            Planner.Plan(_currentIndex, Sim.DistanceToSeam(ExitDir.Left), Sim.DistanceToSeam(ExitDir.Right), Streamer.Resident, _load, _unload);
            for (int i = 0; i < _load.Count; i++) Streamer.Load(_load[i]);
            for (int i = 0; i < _unload.Count; i++) Streamer.Unload(_unload[i]);
        }

        /// <summary>The seam's commit point (end of the step he crossed): the views learn which scene holds him.</summary>
        private void OnSceneChanged(SceneDef from, SceneDef to, ExitDir dir)
        {
            _currentIndex = Planner.IndexOf(to);
            if (to == null)
            {
                if (from != null && dir == ExitDir.Right)
                {
                    Debug.Log("GameHost: he has left " + chapterId + " past " + from.Id + ".", this);
                    ChapterExited?.Invoke();
                }
            }
            else if (!Streamer.IsReady(_currentIndex))
            {
                Debug.LogWarning("GameHost: he crossed into " + to.Id + " before its view loaded (raise the streaming radius?).", this);
                Streamer.Load(_currentIndex);
            }
            CommitViews();
            SceneCommitted?.Invoke(from, to, dir);
        }

        private void CommitViews()
        {
            string current = Sim.Current?.Id;
            var views = SceneView.Loaded;
            for (int i = 0; i < views.Count; i++) views[i].Current = views[i].SceneId == current;
        }

        /// <summary>A view scene finished loading (its root's OnEnable).</summary>
        internal void OnViewLoaded(SceneView view)
        {
            if (view.ChapterId != chapterId)
                Debug.LogWarning("GameHost: view scene " + view.SceneId + " belongs to chapter '" + view.ChapterId + "', not " + chapterId + ".", view);
            view.Current = Sim != null && Sim.Current != null && Sim.Current.Id == view.SceneId;
        }

        // ---- Cues (§3.1 #10–#11) ------------------------------------------------------------------------------------------
        private void Dispatch(IReadOnlyList<Cue> cues)
        {
            for (int i = 0; i < cues.Count; i++)
            {
                Cue cue = cues[i];
                CueRoute r = _routes.Resolve(cue.Id);
                switch (r.Kind)
                {
                    case CueKind.Music:
                        if (score != null) score.Play(r.Key, (float)r.FadeIn);
                        break;
                    case CueKind.Moment:
                        PresentMoment(r.Key);
                        break;
                    case CueKind.Voice:
                        if (voices != null)
                        {
                            VoicePlacement p = VoiceCatalog.FindPlacement(r.Key);
                            voices.Play(r.Key, p != null ? VoicePlayOptions.At(p.X, p.EffectiveReach) : VoicePlayOptions.Flat());
                        }
                        break;
                    case CueKind.Sound:
                        SfxPlayer sfx = SfxPlayer.Current;
                        if (sfx != null)
                        {
                            AudioWorld world = AudioWorld.Current;
                            sfx.PlayPanned(r.Key, 1f, world != null ? world.PanForX(Sim.X) : 0f);
                        }
                        break;
                    case CueKind.Shake:
                        if (cameraDriver != null) cameraDriver.Shake(cue.Arg / 100f);       // calm mode drops it there
                        break;
                    case CueKind.Shot:
                        break;                                                           // the shot itself is Core's framing (ChapterPresenter)
                    default:
                        if (_unknownCues.Add(cue.Id.Value)) Debug.LogWarning("GameHost: no presentation for cue '" + cue.Id.Name + "'.", this);
                        break;
                }
                CueRaised?.Invoke(cue);
            }
        }

        /// <summary>
        /// A directed moment Core started this step (DL-04's kin): its director is the scene's (the moment player renders its
        /// Timeline on it), its cue goes on the score, and any voice gives way (<c>startMoment</c>, L950).
        /// </summary>
        private void PresentMoment(string name)
        {
            if (voices != null) voices.Stop(VoiceRules.MomentStopFade);
            MomentDirector director = Presenter.MomentNamed(name);
            if (moments != null)
            {
                if (director != null) moments.UseDirector(director);
                moments.Present(name);
            }
            if (score != null)
            {
                if (score.CanPlay(name)) score.StartMoment(name);
                else score.MomentFailed(name);
            }
        }

        // ---- Pause -------------------------------------------------------------------------------------------------------
        private void OnPauseChanged()
        {
            bool paused = _pause.IsPaused;
            if (paused == _paused) return;
            _paused = paused;
            if (moments != null) moments.SetPaused(paused);
            if (!paused) _tick.Reset();                                          // no burst of steps for the time spent paused
        }
    }
}
