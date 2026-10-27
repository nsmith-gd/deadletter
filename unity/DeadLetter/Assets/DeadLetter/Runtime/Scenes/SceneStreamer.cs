using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// Loads and unloads a chapter's view scenes additively (port_architecture §7) as the GameHost's
    /// <see cref="DeadLetter.Core.Streaming.StreamingPlanner"/> asks. It only moves Unity scenes: the sim is the chapter's
    /// and never notices a load. Scenes are referenced by asset path (<see cref="DeadLetter.Core.Streaming.ChapterScenes"/>),
    /// so each must be in the build profile's scene list (the Editor's scene builder adds them).
    /// <para>States per scene: unloaded → loading → loaded → unloading → unloaded. A scene asked to unload while it is still
    /// loading unloads as soon as it lands; one asked to load while it is unloading loads again after. A scene that is not in
    /// the build list is <b>missing</b>: logged once, then treated as loaded (the game runs on without its art).</para>
    /// <para>A loaded scene is activated at once (its geometry must be visible before he reaches the seam: holding activation
    /// with <c>allowSceneActivation = false</c> would also stall every later async load behind it). Activation is
    /// time-sliced by <see cref="Application.backgroundLoadingPriority"/>, which the GameHost sets Low in play and High
    /// behind a fade.</para>
    /// </summary>
    public sealed class SceneStreamer
    {
        private enum State { Unloaded, Loading, Loaded, Unloading, Missing }

        private readonly string[] _paths;
        private readonly string[] _ids;
        private readonly State[] _state;
        private readonly AsyncOperation[] _ops;
        private readonly bool[] _wanted;
        private readonly bool[] _resident;

        public SceneStreamer(IReadOnlyList<string> sceneIds, IReadOnlyList<string> scenePaths)
        {
            int n = scenePaths.Count;
            _paths = new string[n];
            _ids = new string[n];
            _state = new State[n];
            _ops = new AsyncOperation[n];
            _wanted = new bool[n];
            _resident = new bool[n];
            for (int i = 0; i < n; i++)
            {
                _paths[i] = scenePaths[i];
                _ids[i] = sceneIds[i];
                // Opened by hand next to the bootstrap scene in the Editor (multi-scene editing): already here.
                if (SceneManager.GetSceneByPath(_paths[i]).isLoaded) { _state[i] = State.Loaded; _wanted[i] = true; }
            }
            Refresh();
        }

        public int Count => _paths.Length;

        /// <summary>Per scene: loaded or on its way in (what the planner calls resident).</summary>
        public IReadOnlyList<bool> Resident => _resident;

        /// <summary>Scene <paramref name="i"/> is loaded and activated (or missing from the build: nothing will come).</summary>
        public bool IsReady(int i) => _state[i] == State.Loaded || _state[i] == State.Missing;

        public bool IsMissing(int i) => _state[i] == State.Missing;

        /// <summary>Every scene in <paramref name="scenes"/> is ready.</summary>
        public bool AllReady(List<int> scenes)
        {
            for (int k = 0; k < scenes.Count; k++) if (!IsReady(scenes[k])) return false;
            return true;
        }

        /// <summary>The Unity scene of view <paramref name="i"/> (invalid until loaded).</summary>
        public Scene SceneAt(int i) => SceneManager.GetSceneByPath(_paths[i]);

        /// <summary>Raised when a view scene has loaded (its objects are awake) and when one has unloaded.</summary>
        public event System.Action<int, bool> Changed;

        public void Load(int i)
        {
            _wanted[i] = true;
            if (_state[i] == State.Unloaded) Begin(i);
            Refresh();
        }

        public void Unload(int i)
        {
            _wanted[i] = false;
            if (_state[i] == State.Loaded) BeginUnload(i);
            Refresh();
        }

        /// <summary>Once per frame: finish operations, and start what a change of mind left waiting.</summary>
        public void Poll()
        {
            for (int i = 0; i < _paths.Length; i++)
            {
                AsyncOperation op = _ops[i];
                if (op != null && !op.isDone) continue;
                _ops[i] = null;
                switch (_state[i])
                {
                    case State.Loading:
                        _state[i] = State.Loaded;
                        Changed?.Invoke(i, true);
                        if (!_wanted[i]) BeginUnload(i);
                        break;
                    case State.Unloading:
                        _state[i] = State.Unloaded;
                        Changed?.Invoke(i, false);
                        if (_wanted[i]) Begin(i);
                        break;
                }
            }
            Refresh();
        }

        private void Begin(int i)
        {
            if (SceneUtility.GetBuildIndexByScenePath(_paths[i]) < 0)
            {
                _state[i] = State.Missing;
                Debug.LogWarning("[Streaming] " + _ids[i] + ": " + _paths[i] + " is not in the build profile's scene list. Run Dead Letter → Build → " +
                                 "Scenes → Prologue (it adds every view scene); until then " + _ids[i] + " has no art.");
                return;
            }
            AsyncOperation op = SceneManager.LoadSceneAsync(_paths[i], LoadSceneMode.Additive);
            if (op == null) { _state[i] = State.Missing; Debug.LogError("[Streaming] could not start loading " + _paths[i] + "."); return; }
            _ops[i] = op;
            _state[i] = State.Loading;
        }

        private void BeginUnload(int i)
        {
            Scene s = SceneAt(i);
            AsyncOperation op = s.IsValid() && s.isLoaded ? SceneManager.UnloadSceneAsync(s) : null;
            _ops[i] = op;
            _state[i] = State.Unloading;                    // with no op (already gone) the next Poll completes it
        }

        private void Refresh()
        {
            for (int i = 0; i < _paths.Length; i++)
                _resident[i] = _state[i] == State.Loaded || _state[i] == State.Loading || _state[i] == State.Missing
                               || (_state[i] == State.Unloading && _wanted[i]);
        }

        /// <summary>For logs and the debug overlay: "DL-01 loaded, DL-02 loading, …".</summary>
        public string Describe()
        {
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < _paths.Length; i++)
            {
                if (_state[i] == State.Unloaded) continue;
                if (sb.Length > 0) sb.Append(", ");
                sb.Append(_ids[i]).Append(' ').Append(_state[i].ToString().ToLowerInvariant());
            }
            return sb.Length == 0 ? "(none)" : sb.ToString();
        }
    }
}
