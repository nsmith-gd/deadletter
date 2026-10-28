using System;
using System.Globalization;
using System.Linq;
using DeadLetter.Core.Streaming;
using DeadLetter.Runtime.Dev;
using DeadLetter.Runtime.Platform;
using DeadLetter.Runtime.Scenes;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace DeadLetter.Editor.Capture
{
    /// <summary>
    /// <c>Dead Letter → Capture → Prologue Playthrough</c>: opens <c>DL_Persistent</c>, adds a
    /// <see cref="PlaythroughCapture"/> (in memory; the generated scene is not saved), starts a new game from the opening
    /// (not the slot's checkpoint) and enters Play. Core's bot plays and the shots go to <c>Captures/</c> under the project.
    /// Headless, with the GPU (not <c>-nographics</c>), and without <c>-quit</c> (the editor quits when the run ends):
    /// <code>
    /// Unity.exe -batchmode -projectPath unity/DeadLetter -logFile capture.log
    ///   -executeMethod DeadLetter.Editor.Capture.PlayCapture.Run
    ///   [-captureOut DIR] [-captureSeed N] [-captureHuman] [-captureTimes 0.1,3,10] [-captureNoMarks]
    ///   [-captureMax SECONDS] [-captureSize 1280x720]
    /// </code>
    /// tools/capture/README.md has the comparison with the prototype.
    /// </summary>
    [InitializeOnLoad]
    public static class PlayCapture
    {
        private const string ActiveKey = "DeadLetter.PlayCapture.Active";
        private const string QuitKey = "DeadLetter.PlayCapture.Quit";

        static PlayCapture()
        {
            EditorApplication.playModeStateChanged += OnPlayModeChanged;
        }

        [MenuItem("Dead Letter/Capture/Prologue Playthrough")]
        public static void RunMenu() => Begin(new Options(), quitAfter: false);

        /// <summary>The headless entry point (<c>-executeMethod</c>); reads the <c>-capture…</c> arguments.</summary>
        public static void Run()
        {
            var o = new Options();
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length; i++)
            {
                string next = i + 1 < args.Length ? args[i + 1] : "";
                switch (args[i])
                {
                    case "-captureOut": o.OutDir = next; break;
                    case "-captureSeed": o.Seed = uint.Parse(next, CultureInfo.InvariantCulture); break;
                    case "-captureHuman": o.Mechanical = false; break;
                    case "-captureNoMarks": o.Marks = false; break;
                    case "-captureMax": o.MaxSeconds = double.Parse(next, CultureInfo.InvariantCulture); break;
                    case "-captureTimes":
                        o.Times = next.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)
                                      .Select(s => double.Parse(s, CultureInfo.InvariantCulture)).OrderBy(t => t).ToArray();
                        break;
                    case "-captureSize":
                        string[] wh = next.Split('x');
                        o.Width = int.Parse(wh[0], CultureInfo.InvariantCulture);
                        o.Height = int.Parse(wh[1], CultureInfo.InvariantCulture);
                        break;
                }
            }
            Begin(o, quitAfter: Application.isBatchMode);
        }

        private sealed class Options
        {
            public string OutDir = "Captures/unity";
            public uint Seed = 1;
            public bool Mechanical = true;
            public bool Marks = true;
            public double MaxSeconds = 600;
            public double[] Times = { 0.1, 1, 3, 6, 10, 15, 20, 30, 45, 60, 90, 120, 150, 180, 240 };
            public int Width = 1280, Height = 720;
        }

        private static void Begin(Options o, bool quitAfter)
        {
            if (EditorApplication.isPlaying) { Debug.LogError("[Capture] Stop Play first."); return; }
            EditorSceneManager.OpenScene(ChapterScenes.BootstrapPath, OpenSceneMode.Single);
            var host = UnityEngine.Object.FindFirstObjectByType<GameHost>();
            if (host == null)
            {
                Debug.LogError("[Capture] " + ChapterScenes.BootstrapPath + " has no GameHost: run Dead Letter → Build → Scenes → Prologue first.");
                if (quitAfter) EditorApplication.Exit(1);
                return;
            }
            var so = new SerializedObject(host);
            so.FindProperty("continueFromSave").boolValue = false;
            so.FindProperty("startFromOpening").boolValue = true;
            so.FindProperty("startAt").stringValue = "";
            so.ApplyModifiedPropertiesWithoutUndo();

            // A headless editor never has focus: the desktop's pause-on-focus-loss would hold time at 0.
            var platform = UnityEngine.Object.FindFirstObjectByType<PlatformServicesHost>();
            if (platform != null)
            {
                var ps = new SerializedObject(platform);
                ps.FindProperty("pauseOnFocusLoss").boolValue = false;
                ps.ApplyModifiedPropertiesWithoutUndo();
            }

            var capture = new GameObject("PlaythroughCapture").AddComponent<PlaythroughCapture>();
            capture.outDir = o.OutDir;
            capture.seed = o.Seed;
            capture.mechanical = o.Mechanical;
            capture.captureMarks = o.Marks;
            capture.maxPlaySeconds = o.MaxSeconds;
            capture.times = o.Times;
            capture.width = o.Width;
            capture.height = o.Height;

            SessionState.SetBool(ActiveKey, true);
            SessionState.SetBool(QuitKey, quitAfter);
            EditorApplication.EnterPlaymode();
        }

        private static void OnPlayModeChanged(PlayModeStateChange change)
        {
            if (!SessionState.GetBool(ActiveKey, false)) return;
            switch (change)
            {
                case PlayModeStateChange.EnteredPlayMode:
                    var capture = UnityEngine.Object.FindFirstObjectByType<PlaythroughCapture>();
                    if (capture == null) { Debug.LogError("[Capture] The capture did not survive entering Play."); EditorApplication.ExitPlaymode(); return; }
                    capture.Finished += EditorApplication.ExitPlaymode;
                    break;
                case PlayModeStateChange.EnteredEditMode:
                    SessionState.EraseBool(ActiveKey);
                    bool quit = SessionState.GetBool(QuitKey, false);
                    SessionState.EraseBool(QuitKey);
                    // Drop the in-memory capture object and GameHost overrides: the generated scene stays as built.
                    EditorSceneManager.OpenScene(ChapterScenes.BootstrapPath, OpenSceneMode.Single);
                    if (quit) EditorApplication.Exit(0);
                    break;
            }
        }
    }
}
