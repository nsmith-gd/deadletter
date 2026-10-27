using System;
using System.Collections.Generic;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// The root of one view scene (<c>Assets/Scenes/&lt;Chapter&gt;/&lt;SceneId&gt;.unity</c>, built by the Editor's scene
    /// builder): which <see cref="DeadLetter.Core.Scenes.SceneDef"/> it shows, and whether that scene holds D-17 now. The
    /// GameHost commits a scene on <c>ChapterSim.SceneChanged</c> by setting <see cref="Current"/>; per-scene presentation that
    /// should only run while he is in the scene (light proxies, emitters, U-15/U-16) listens to <see cref="CurrentChanged"/>.
    /// A view never holds sim state: unloading it loses nothing.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class SceneView : MonoBehaviour
    {
        [SerializeField] private string chapterId;
        [SerializeField] private string sceneId;

        private static readonly List<SceneView> _loaded = new List<SceneView>();
        private bool _current;

        public string ChapterId => chapterId;
        public string SceneId => sceneId;
        /// <summary>The views whose scenes are loaded.</summary>
        public static IReadOnlyList<SceneView> Loaded => _loaded;

        /// <summary>The scene holds D-17 (committed at the end of the step he crossed into it).</summary>
        public bool Current
        {
            get => _current;
            internal set
            {
                if (_current == value) return;
                _current = value;
                CurrentChanged?.Invoke(value);
            }
        }

        public event Action<bool> CurrentChanged;

        public void Configure(string chapter, string scene)
        {
            chapterId = chapter;
            sceneId = scene;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() => _loaded.Clear();

        private void OnEnable()
        {
            if (!_loaded.Contains(this)) _loaded.Add(this);
            GameHost host = GameHost.Instance;
            if (host != null) host.OnViewLoaded(this);
        }

        private void OnDisable() => _loaded.Remove(this);

        public static SceneView Find(string id)
        {
            for (int i = 0; i < _loaded.Count; i++) if (_loaded[i].sceneId == id) return _loaded[i];
            return null;
        }
    }
}
