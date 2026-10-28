using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using DeadLetter.Editor.Art;
using DeadLetter.Runtime;
using DeadLetter.Runtime.Art;
using DeadLetter.Runtime.Audio;
using DeadLetter.Runtime.Camera;
using DeadLetter.Runtime.Platform;
using DeadLetter.Runtime.Scenes;
using DeadLetter.Runtime.Settings;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
// UnityEditor has a SceneView too.
using SceneView = DeadLetter.Runtime.Scenes.SceneView;

namespace DeadLetter.Editor.Builders
{
    /// <summary>
    /// <c>Dead Letter → Build → Scenes → Prologue</c> (U-20, issue #16) and <c>→ Attendance</c> (U-22b, #50): generates a
    /// chapter's Unity scenes from Core's <see cref="ChapterDef"/> (port_architecture §6.2: nothing in a generated
    /// <c>.unity</c> is hand-placed; hand edits are lost on the next build, by design):
    /// <list type="bullet">
    /// <item><c>Assets/Scenes/DL_Persistent.unity</c> (§7): the <see cref="GameHost"/> and the boot systems
    /// (<see cref="PlatformServicesHost"/>, <see cref="SettingsStore"/>, the fade), D-17 from <c>Assets/Art/D17/d17.glb</c> with
    /// its Animator controller and <see cref="D17Controller"/>, the camera with <see cref="LaneCameraDriver"/>, and the audio
    /// (music clock, score, SFX, voices, audio world, the directed-moment player).</item>
    /// <item><c>Assets/Scenes/&lt;Chapter&gt;/&lt;SceneId&gt;.unity</c>, one per <see cref="SceneDef"/>: a <see cref="SceneView"/>
    /// root and the U-12 region prefab (<c>Assets/Art/&lt;region&gt;/&lt;region&gt;.prefab</c>, <see cref="ArtPrefabBuilder"/>)
    /// at world positions, with a <see cref="MechanismView"/> on every <c>MECH_</c> node of a mechanism the chapter simulates
    /// (bindings: Core's <see cref="MechanismViewBindings"/>). Geometry no mechanism moves is marked batching-static.</item>
    /// </list>
    /// Every scene path goes into the build profile's scene list (the bootstrap first), so the runtime streamer can load them.
    /// Reproducible: the same Core definitions and art give the same scenes; a scene whose art is not imported is still
    /// written (empty but for its root), and the log says what to import.
    /// </summary>
    public static class ChapterSceneBuilder
    {
        public const string D17Glb = D17AnimatorBuilder.GlbPath;
        public const string D17ControllerAsset = D17AnimatorBuilder.ControllerPath;
        public const string InputActions = "Assets/DeadLetter/Runtime/Input/DeadLetter.inputactions";
        public const string SfxBankPath = "Assets/Audio/SfxBank.asset";

        [MenuItem("Dead Letter/Build/Scenes/Prologue")]
        public static void BuildPrologue() => BuildChapter(ChapterDefs.PrologueId);

        /// <summary>Chapter 1's first checkpoint, where Play starts in the editor (docs/unity/chapter1_editor_check.md).</summary>
        public const string AttendanceStart = "school";

        /// <summary>
        /// Chapter 1 Attendance: its scenes as <see cref="BuildChapter"/> builds any chapter's, and Play starts at
        /// <see cref="AttendanceStart"/> (the host's <c>startAt</c>; set it to any chapter 1 checkpoint to start there).
        /// </summary>
        [MenuItem("Dead Letter/Build/Scenes/Attendance")]
        public static void BuildAttendance()
        {
            BuildChapter(ChapterDefs.AttendanceId);
            StartAt(ChapterDefs.AttendanceId, AttendanceStart);
        }

        /// <summary>Chapter 2's first checkpoint, where Play starts in the editor.</summary>
        public const string SomeoneHomeStart = "ring_a";

        /// <summary>
        /// Chapter 2 Someone Home, as <see cref="BuildAttendance"/>. Its view scenes stay in the build list when chapter 1 is
        /// built after it, so the bootstrap then plays chapter 1 on into chapter 2 across the seam (#51).
        /// </summary>
        [MenuItem("Dead Letter/Build/Scenes/Someone Home")]
        public static void BuildSomeoneHome()
        {
            BuildChapter(ChapterDefs.SomeoneHomeId);
            StartAt(ChapterDefs.SomeoneHomeId, SomeoneHomeStart);
        }

        /// <summary>Sets the open bootstrap's <c>startAt</c>, if it is <paramref name="chapterId"/>'s (a cancelled build leaves another).</summary>
        private static void StartAt(string chapterId, string checkpoint)
        {
            Scene scene = SceneManager.GetActiveScene();
            var host = Object.FindFirstObjectByType<GameHost>();
            if (scene.path != ChapterScenes.BootstrapPath || host == null) return;
            if (new SerializedObject(host).FindProperty("chapterId")?.stringValue != chapterId) return;
            Set(host, "startAt", checkpoint);
            EditorSceneManager.SaveScene(scene);
            Debug.Log("[Scenes] " + chapterId + ": Play starts at '" + checkpoint + "' (GameHost.startAt).");
        }

        /// <summary>Builds every scene of chapter <paramref name="chapterId"/> and opens its bootstrap. Returns the problems found.</summary>
        public static List<string> BuildChapter(string chapterId)
        {
            var problems = new List<string>();
            ChapterDef def = ChapterScenes.Create(chapterId);
            if (def == null) { Debug.LogError("[Scenes] No chapter '" + chapterId + "'."); return problems; }
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) { Debug.Log("[Scenes] Cancelled."); return problems; }

            EnsureFolder(ChapterScenes.Root);
            EnsureFolder(ChapterScenes.Root + "/" + ChapterScenes.Folder(chapterId));

            var mechanismIds = new HashSet<string>();
            foreach (SceneDef s in def.Scenes) foreach (MechanismDef m in s.Mechanisms) mechanismIds.Add(m.Id.Value);

            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null)
                problems.Add(ArtIndex.IndexPath + " not found: no scene gets art. Run tools/unity_export/export_regions.py, then Dead Letter → Art → Build Region Prefabs.");

            var report = new StringBuilder();
            var paths = new List<string>();
            var placedRegions = new HashSet<string>();
            try
            {
                for (int i = 0; i < def.Scenes.Count; i++)
                {
                    SceneDef scene = def.Scenes[i];
                    EditorUtility.DisplayProgressBar("Dead Letter: chapter scenes", scene.Id, (float)i / (def.Scenes.Count + 1));
                    string path = ChapterScenes.ScenePath(chapterId, scene.Id);
                    report.Append("\n  ").Append(BuildViewScene(chapterId, scene, path, index, mechanismIds, placedRegions, problems));
                    paths.Add(path);
                }
                EditorUtility.DisplayProgressBar("Dead Letter: chapter scenes", ChapterScenes.BootstrapName, 1f);
                BuildBootstrap(chapterId, problems);
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }

            SetBuildScenes(paths);
            AssetDatabase.SaveAssets();
            EditorSceneManager.OpenScene(ChapterScenes.BootstrapPath, OpenSceneMode.Single);

            foreach (string p in problems) Debug.LogWarning("[Scenes] " + p);
            Debug.Log("[Scenes] " + chapterId + ": " + ChapterScenes.BootstrapPath + " and " + paths.Count + " view scenes, " + problems.Count +
                      " warnings." + report + "\nPress Play in " + ChapterScenes.BootstrapPath + ".");
            return problems;
        }

        // ---- One view scene per SceneDef ----------------------------------------------------------------------------------

        private static string BuildViewScene(string chapterId, SceneDef def, string path, ArtIndex index, HashSet<string> mechanismIds,
            HashSet<string> placedRegions, List<string> problems)
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject(def.Id);
            root.AddComponent<SceneView>().Configure(chapterId, def.Id);
            ChapterSeams.Origin(chapterId, out double originX, out double originY);           // the chapter's datum in the world (#51)
            root.transform.position = new Vector3((float)originX, (float)originY, 0f);

            string line = def.Id + ": ";
            ArtIndexEntry entry = ArtFor(index, def.Id);
            if (entry == null)
            {
                problems.Add(def.Id + ": no region in " + ArtIndex.IndexPath + " lists this scene: it has no art (export it with tools/unity_export/export_regions.py).");
                line += "no art exported";
            }
            else if (placedRegions.Contains(entry.name))
            {
                line += "art " + entry.name + " is in an earlier scene of its stretch (it streams with it)";
            }
            else
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(entry.PrefabPath);
                if (prefab == null)
                {
                    problems.Add(def.Id + ": art for this scene isn't imported: no " + entry.PrefabPath + ". Import " + entry.AssetPath +
                                 " (glTFast) and run Dead Letter → Art → Build Region Prefabs, then build the scenes again.");
                    line += "ART NOT IMPORTED (" + entry.PrefabPath + ")";
                }
                else
                {
                    placedRegions.Add(entry.name);
                    var art = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
                    art.transform.SetParent(root.transform, false);
                    art.transform.localPosition = Vector3.zero;                      // lane coordinates are world coordinates (§7: no re-centring)
                    line += "art " + entry.name + ", " + AddViews(art, mechanismIds, def.Id, problems);
                }
            }

            EditorSceneManager.SaveScene(scene, path);
            return line;
        }

        /// <summary>A view on every <c>MECH_</c> node of a simulated mechanism; batching-static on everything else.</summary>
        private static string AddViews(GameObject art, HashSet<string> mechanismIds, string sceneId, List<string> problems)
        {
            int views = 0, staticNodes = 0, unbound = 0, notSimulated = 0;
            var moved = new HashSet<Transform>();
            foreach (ArtMarker marker in art.GetComponentsInChildren<ArtMarker>(true))
            {
                if (marker.prefix != "MECH") continue;
                foreach (Transform t in marker.GetComponentsInChildren<Transform>(true)) moved.Add(t);   // never batched: Core may move it
                if (!mechanismIds.Contains(marker.id)) { notSimulated++; continue; }
                var bindings = MechanismViewBindings.For(marker.type, marker.id, marker.part);
                if (bindings.Length == 0) { unbound++; continue; }
                var channels = new MechanismView.Channel[bindings.Length];
                for (int i = 0; i < bindings.Length; i++) channels[i] = MechanismView.From(bindings[i]);
                var view = marker.GetComponent<MechanismView>();
                if (view == null) view = marker.gameObject.AddComponent<MechanismView>();
                view.Configure(marker.id, marker.part, channels);
                views++;
            }
            foreach (Renderer r in art.GetComponentsInChildren<Renderer>(true))
            {
                if (moved.Contains(r.transform)) { GameObjectUtility.SetStaticEditorFlags(r.gameObject, 0); continue; }
                GameObjectUtility.SetStaticEditorFlags(r.gameObject, StaticEditorFlags.BatchingStatic);
                staticNodes++;
            }
            if (views == 0) problems.Add(sceneId + ": no MECH_ node of a simulated mechanism was found in the art (is the export current?).");
            return views + " mechanism views (" + unbound + " MECH_ nodes static by design, " + notSimulated + " of mechanisms not simulated yet), " +
                   staticNodes + " static renderers";
        }

        private static ArtIndexEntry ArtFor(ArtIndex index, string sceneId)
        {
            if (index?.regions == null) return null;
            foreach (ArtIndexEntry e in index.regions)
            {
                if (!e.IsSet || e.scenes == null) continue;
                foreach (string s in e.scenes) if (s == sceneId) return e;
            }
            return null;
        }

        // ---- The bootstrap scene --------------------------------------------------------------------------------------------

        private static void BuildBootstrap(string chapterId, List<string> problems)
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            // The bootstrap stays the active scene, so its lighting settings are the game's: no ambient (U-15's light pool
            // lights the sets), fog driven by the camera rig each frame.
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.06f, 0.06f, 0.07f);
            RenderSettings.skybox = null;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = Color.black;                           // LookVolume sets the page's 0x040505 at runtime

            Object inputActions = AssetDatabase.LoadAssetAtPath<Object>(InputActions);   // an InputActionAsset (the Editor asmdef has no Input System reference)
            if (inputActions == null) problems.Add("No input actions at " + InputActions + ": D-17 will not respond to input.");
            Object bank = AssetDatabase.LoadAssetAtPath<Object>(SfxBankPath);
            if (bank == null) problems.Add("No " + SfxBankPath + ": run Dead Letter → Audio → Import Audio for music and sounds (the game runs silent without).");

            // Systems (DL_Persistent, §7).
            var systems = new GameObject("Systems");
            var platform = systems.AddComponent<PlatformServicesHost>();
            var settings = systems.AddComponent<SettingsStore>();
            var host = systems.AddComponent<GameHost>();
            var fade = systems.AddComponent<ScreenFade>();

            var audio = new GameObject("Audio");
            var clock = audio.AddComponent<AudioDspMusicClock>();
            var score = audio.AddComponent<MusicDirector>();
            var sfx = audio.AddComponent<SfxPlayer>();
            var voices = audio.AddComponent<VoicePlayer>();
            var world = audio.AddComponent<AudioWorld>();
            var moments = audio.AddComponent<DirectedMomentPlayer>();

            // D-17.
            GameObject d17;
            var d17Asset = AssetDatabase.LoadAssetAtPath<GameObject>(D17Glb);
            if (d17Asset != null) d17 = (GameObject)PrefabUtility.InstantiatePrefab(d17Asset, scene);
            else
            {
                d17 = new GameObject();
                problems.Add("No " + D17Glb + " (glTFast import): D-17 is an empty placeholder.");
            }
            d17.name = "D17";
            int d17Slots = ArtMaterials.ApplyToHierarchy(d17);   // the prototype's paint, not glTFast's grey (L527)
            if (d17Slots == 0 && d17Asset != null) problems.Add("D-17: no material matched the prototype's tables (ArtMaterials.ForSource).");
            d17.transform.SetPositionAndRotation(Vector3.zero, Quaternion.Euler(0f, 90f, 0f));
            var animator = d17.GetComponentInChildren<Animator>();
            if (animator == null) animator = d17.AddComponent<Animator>();
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(D17ControllerAsset);
            if (controller != null) animator.runtimeAnimatorController = controller;
            else problems.Add("No " + D17ControllerAsset + ": run Dead Letter → Build → D17 Animator, then build the scenes again.");
            var player = d17.AddComponent<D17Controller>();

            // Camera (Core's rig, rendered straight to the Camera: no Cinemachine camera yet).
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<UnityEngine.Camera>();
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 80f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Color.black;
            camGo.AddComponent<AudioListener>();
            var driver = camGo.AddComponent<LaneCameraDriver>();
            var look = camGo.AddComponent<LookVolume>();   // adds the global Volume it fills (the prototype's post, PostLook)

            // A temporary key light so the sets read before U-15's light pool exists.
            var keyGo = new GameObject("Temporary Key Light (U-15 replaces)");
            var key = keyGo.AddComponent<Light>();
            key.type = LightType.Directional;
            key.intensity = 0.6f;
            keyGo.transform.rotation = Quaternion.Euler(35f, 20f, 0f);

            // Wiring (serialized fields by name; a renamed field is an error in the log).
            Set(platform, "player", player);
            Set(platform, "moments", moments);
            Set(settings, "actions", inputActions);
            Set(settings, "postVolume", camGo.GetComponent("Volume"));   // brightness and calm bloom on LookVolume's profile
            Set(look, "volume", camGo.GetComponent("Volume"));
            Set(host, "chapterId", chapterId);
            Set(host, "player", player);
            Set(host, "cameraDriver", driver);
            Set(host, "moments", moments);
            Set(host, "score", score);
            Set(host, "voices", voices);
            Set(host, "audioWorld", world);
            Set(host, "fade", fade);
            Set(host, "platformHost", platform);
            Set(player, "actions", inputActions);
            Set(player, "animator", animator);
            Set(driver, "player", player);
            Set(driver, "moments", moments);
            Set(driver, "targetCamera", cam);
            Set(score, "bank", bank);
            Set(score, "musicClock", clock);
            Set(sfx, "bank", bank);
            Set(voices, "bank", bank);
            Set(voices, "music", score);
            Set(voices, "moments", moments);
            Set(world, "listener", d17.transform);
            Set(world, "panCamera", cam);
            Set(moments, "player", player);
            Set(moments, "musicClock", clock);
            Set(moments, "score", score);
            Set(moments, "voices", voices);
            Set(moments, "cameraDriver", driver);
            problems.Add("No audio mixer yet (U-16): SettingsStore's volumes do nothing until one is assigned.");

            EditorSceneManager.SaveScene(scene, ChapterScenes.BootstrapPath);
        }

        // ---- Helpers -----------------------------------------------------------------------------------------------------

        /// <summary>The bootstrap first, then the chapter's view scenes in lane order, then any other scenes already listed.</summary>
        private static void SetBuildScenes(List<string> viewPaths)
        {
            var ours = new HashSet<string>(viewPaths) { ChapterScenes.BootstrapPath };
            var list = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(ChapterScenes.BootstrapPath, true) };
            foreach (string p in viewPaths) list.Add(new EditorBuildSettingsScene(p, true));
            foreach (EditorBuildSettingsScene s in EditorBuildSettings.scenes) if (!ours.Contains(s.path)) list.Add(s);
            EditorBuildSettings.scenes = list.ToArray();
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        private static void Set(Object target, string field, Object value)
        {
            var so = new SerializedObject(target);
            SerializedProperty p = so.FindProperty(field);
            if (p == null) { Debug.LogError("[Scenes] " + target.GetType().Name + " has no serialized field '" + field + "'."); return; }
            p.objectReferenceValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void Set(Object target, string field, string value)
        {
            var so = new SerializedObject(target);
            SerializedProperty p = so.FindProperty(field);
            if (p == null) { Debug.LogError("[Scenes] " + target.GetType().Name + " has no serialized field '" + field + "'."); return; }
            p.stringValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
