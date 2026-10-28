using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Art;
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
    /// <c>Dead Letter → Build → Scenes → Prologue</c> (U-20, issue #16): generates a chapter's Unity scenes from Core's
    /// <see cref="ChapterDef"/> (port_architecture §6.2: nothing in a generated <c>.unity</c> is hand-placed; hand edits are
    /// lost on the next build, by design):
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
                    string why = def.Id + ": art for this scene isn't imported: no " + entry.PrefabPath + " (" +
                                 ArtPrefabBuilder.GltfImportReport(entry.AssetPath) + "). Import " + entry.AssetPath +
                                 " (glTFast) and run Dead Letter → Art → Build Region Prefabs, then build the scenes again.";
                    problems.Add(why);
                    Debug.LogError("[Scenes] " + why);   // an empty world is not a warning
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
                var bindings = MechanismViewBindings.For(marker.type, marker.part);
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
            // The bootstrap stays the active scene, so its lighting settings are the game's. The prototype's (buildLights,
            // L1460–L1463; scene L350–L351): a hemisphere light 0x26332f / 0x0b0b0a at 0.45, a rim light 0x8db4c8 at 0.35, a
            // 0x030404 background and 0x040505 exp² fog whose density the camera rig drives each frame; the sets' real light is
            // the LGT_ light pool (~160 lights in code, U-15, not ported yet). Until then the hemisphere stands in as a
            // trilight ambient, a little brighter than the prototype's so the sets read without the pool and AgX at 1.4.
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = Hex(0x26332f) * 1.6f;
            RenderSettings.ambientEquatorColor = Color.Lerp(Hex(0x26332f), Hex(0x0b0b0a), 0.5f) * 1.6f;
            RenderSettings.ambientGroundColor = Hex(0x0b0b0a) * 1.6f;
            RenderSettings.ambientIntensity = 1f;
            RenderSettings.skybox = null;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = Hex(0x040505);

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
            int recoloured = ApplyPrototypeMaterials(d17);   // D-17's GLB has no colours of its own (materialFor's tables do)
            if (d17Asset != null && recoloured == 0) problems.Add("D-17: no material matched PrototypeMaterials; he stays glTFast's untinted white/grey.");
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
            cam.backgroundColor = Hex(0x030404);                               // scene.background, L350
            camGo.AddComponent<AudioListener>();
            var driver = camGo.AddComponent<LaneCameraDriver>();

            // A temporary key light so the sets read before U-15's light pool exists.
            var keyGo = new GameObject("Temporary Key Light (U-15 replaces)");
            var key = keyGo.AddComponent<Light>();
            key.type = LightType.Directional;
            key.intensity = 0.6f;
            keyGo.transform.rotation = Quaternion.Euler(35f, 20f, 0f);
            // The prototype's rim light (L1462): from (5, 3, −8) toward (3, 0, 0) in its axes; Unity z = −z (§0.2).
            var rimGo = new GameObject("Rim Light (index.html L1462)");
            var rim = rimGo.AddComponent<Light>();
            rim.type = LightType.Directional;
            rim.color = Hex(0x8db4c8);
            rim.intensity = 0.35f;
            rimGo.transform.rotation = Quaternion.LookRotation(new Vector3(3f, 0f, 0f) - new Vector3(5f, 3f, 8f));

            // Wiring (serialized fields by name; a renamed field is an error in the log).
            Set(platform, "player", player);
            Set(platform, "moments", moments);
            Set(settings, "actions", inputActions);
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

        /// <summary>
        /// Swaps every material of <paramref name="go"/> whose name the prototype's tables know (<see cref="PrototypeMaterials"/>;
        /// D-17's are <c>Name.003</c>) for the shared URP Lit asset of <see cref="ArtMaterials"/>. glTFast's own materials stay
        /// for the rest (the decals with their textures: the mug, the claw stamp, the parcel label). Returns the slots swapped.
        /// </summary>
        private static int ApplyPrototypeMaterials(GameObject go)
        {
            int swapped = 0;
            var cache = new Dictionary<string, Material>();
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null || !PrototypeMaterials.Lookup(mats[i].name, out _)) continue;
                    string name = PrototypeMaterials.BaseName(mats[i].name);
                    if (!cache.TryGetValue(name, out Material urp))
                        cache[name] = urp = ArtMaterials.GetOrCreate(new ArtMaterialDef { name = name });
                    if (urp == null) continue;
                    mats[i] = urp;
                    changed = true;
                    swapped++;
                }
                if (changed) r.sharedMaterials = mats;
            }
            return swapped;
        }

        private static Color Hex(int rgb) => new Color(((rgb >> 16) & 255) / 255f, ((rgb >> 8) & 255) / 255f, (rgb & 255) / 255f);

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
