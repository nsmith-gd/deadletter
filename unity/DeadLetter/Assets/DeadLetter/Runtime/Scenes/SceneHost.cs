using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Simulation;
using DeadLetter.Runtime.Camera;
using DeadLetter.Runtime.Platform;
using DeadLetter.Runtime.Save;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// Runs one ported scene (U-20): owns Core's <see cref="SceneRunner"/> and its fixed 60 Hz tick (§3.1), and feeds the
    /// thin adapters around it. It decides nothing (§2 "Rules").
    /// <list type="bullet">
    /// <item><see cref="D17Controller"/> (hosted): input in, transform and Animator out.</item>
    /// <item><see cref="LaneCameraDriver"/> (bound): renders the runner's camera rig.</item>
    /// <item><see cref="DirectedMomentPlayer"/> (hosted): cue and Timeline for moments Core starts.</item>
    /// <item><see cref="MechanismView"/>s read the runner's graph in LateUpdate.</item>
    /// <item><see cref="CheckpointTrigger.Service"/> is the runner's service (pause card, moment reloads).</item>
    /// </list>
    /// Built by the Editor's SceneBuilder; one per scene for now. §7's streaming (one persistent runner for the chapter,
    /// scenes as views) replaces this per-scene ownership when more than one scene is ported.
    /// </summary>
    [DisallowMultipleComponent]
    // After D17Controller's Update (it latches this frame's presses) so a press is stepped the same frame; the adapters
    // accept being attached after their own Awake. Their LateUpdate then renders this frame's steps.
    [DefaultExecutionOrder(10)]
    public sealed class SceneHost : MonoBehaviour
    {
        [Tooltip("A SceneCatalog id, e.g. DL-01.")]
        [SerializeField] private string sceneId = "DL-01";
        [SerializeField] private D17Controller player;
        [SerializeField] private LaneCameraDriver cameraDriver;
        [SerializeField] private DirectedMomentPlayer moments;
        [Tooltip("Optional: the parcel label on D-17 (the opening camera starts on its centre, captureChest L7649).")]
        [SerializeField] private Transform openingChest;
        [SerializeField] private int saveSlot;
        [Tooltip("Continue from the save slot when it holds this scene; otherwise a new game.")]
        [SerializeField] private bool continueFromSave = true;
        [SerializeField] private bool playOpening = true;
        [Tooltip("Calm mode (accessibility): softer flicker, no shake. U-17's options will own this.")]
        [SerializeField] private bool calm;

        private FixedTick _tick;

        /// <summary>The running scene; null before Awake or when the id is not ported.</summary>
        public SceneRunner Runner { get; private set; }

        /// <summary>Cues fired by a Core step (music, voice); U-16's audio director subscribes.</summary>
        public event Action<string> CueRequested;

        /// <summary>He walked out through the scene's exit (the host of §7 streams the next scene).</summary>
        public event Action<string> ExitReached;

        private void Awake()
        {
            SceneDefinition def = SceneCatalog.Create(sceneId);
            if (def == null) { Debug.LogError("SceneHost: no Core scene definition for '" + sceneId + "'.", this); enabled = false; return; }
            if (openingChest != null && def.Opening != null)
            {
                Vector3 c = openingChest.position;
                def.Opening.Chest = new Vec3(c.x, c.y, -c.z);              // Core camera axes are the prototype's (§0.2)
            }

            ISaveStore store = new AtomicFileStore(new LocalFileSystem());
            // Unity's null check: an unassigned field is a "fake null" object to C#'s != in the Editor.
            AudioDspMusicClock clock = moments != null && moments.MusicClock ? moments.MusicClock : null;
            Runner = new SceneRunner(def, store, saveSlot, clock);
            Runner.Graph.Calm = calm;
            _tick = new FixedTick(SceneRunner.StepSeconds, 4);

            if (player != null) player.AttachToHost(Runner.Motor, Runner.Resolver, () => (float)_tick.Alpha);
            if (cameraDriver != null) cameraDriver.BindRig(Runner.Camera);
            if (moments != null) moments.UseDirector(Runner.Moments);
            Runner.Checkpoints.Reloaded += _ => { if (player != null) player.SnapToMotor(); if (cameraDriver != null) cameraDriver.Snap(); };
            CheckpointTrigger.Service = Runner.Checkpoints;
        }

        private void Start()
        {
            if (Runner == null) return;
            bool resumed = false;
            if (continueFromSave) resumed = Runner.Continue();
            if (!resumed) Runner.NewGame(playOpening);   // the opening's moment and cue are reported with the first step
        }

        private void Update()
        {
            if (Runner == null) return;
            if (cameraDriver != null) Runner.Aspect = cameraDriver.Aspect;
            int steps = _tick.Advance(Time.deltaTime);
            for (int i = 0; i < steps; i++)
            {
                var input = player != null ? player.TakeInput() : default;
                Runner.Step(input);
                if (player != null) player.OnHostStepped(SceneRunner.StepSeconds);
                Present();
            }
            if (player != null)
            {
                player.OverrideClip = Runner.InOpening ? "Opening" : null;
                player.OverrideClipTime = Runner.OpeningFrame / 24.0;
            }
            Runner.Checkpoints.Update(Time.unscaledDeltaTime, playing: true);
        }

        /// <summary>Hands this step's Core outcomes to the presentation adapters.</summary>
        private void Present()
        {
            if (Runner.MomentStartedThisStep != null && moments != null) moments.Present(Runner.MomentStartedThisStep.Name);
            var cues = Runner.CuesThisStep;
            for (int i = 0; i < cues.Count; i++) CueRequested?.Invoke(cues[i]);
            if (Runner.ExitedThisStep) ExitReached?.Invoke(Runner.Definition.Exit.NextScene);
        }

        private void OnApplicationPause(bool paused) { if (paused) Runner?.Checkpoints.Flush(); }
        private void OnApplicationQuit() { Runner?.Checkpoints.Flush(); }

        private void OnDestroy()
        {
            if (Runner != null && CheckpointTrigger.Service == Runner.Checkpoints) CheckpointTrigger.Service = null;
        }
    }
}
