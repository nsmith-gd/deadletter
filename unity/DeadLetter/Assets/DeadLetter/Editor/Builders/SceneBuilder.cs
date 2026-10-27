using System.Collections.Generic;
using System.IO;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Prologue;
using DeadLetter.Runtime;
using DeadLetter.Runtime.Camera;
using DeadLetter.Runtime.Scenes;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DeadLetter.Editor.Builders
{
    /// <summary>
    /// Generates a scene's <c>.unity</c> file from its Core <see cref="SceneDefinition"/> (port_architecture §6.2:
    /// "nothing in a .unity file is hand-placed except what a builder regenerates"; hand edits are lost by design):
    /// the region art prefab (asset_conventions.md, PR #24), D-17, the camera, the <see cref="SceneHost"/> and its
    /// adapters, and one <see cref="MechanismView"/> per <c>MECH_</c> node the definition's views name.
    /// One menu item per ported scene; the work is <see cref="Build"/>.
    /// <para>Written without an Editor to compile against (U-20 slice): APIs used are long-standing ones, but the result
    /// must be opened once in Unity 6 and checked (see docs/unity/scene_port_guide.md, "Unity checks").</para>
    /// </summary>
    public static class SceneBuilder
    {
        public const string D17Glb = "Assets/Art/D17/d17.glb";
        public const string D17AnimatorAsset = D17AnimatorBuilder.ControllerPath;
        public const string InputActions = "Assets/DeadLetter/Runtime/Input/DeadLetter.inputactions";

        [MenuItem("Dead Letter/Build/Scenes/DL-01")]
        public static void BuildDl01() => Build(new Dl01Wake(), "Assets/Scenes/Prologue/DL01.unity");

        /// <summary>Builds and saves <paramref name="scenePath"/> from <paramref name="def"/>. Returns the problems found (also logged).</summary>
        public static List<string> Build(SceneDefinition def, string scenePath)
        {
            var problems = new List<string>();
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // Art: Assets/Art/<region>/<region>.prefab, built by #24's ArtPrefabBuilder at the §0.2 positions.
            string artPath = "Assets/Art/" + def.ArtRegion + "/" + def.ArtRegion + ".prefab";
            var artPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(artPath);
            GameObject art = null;
            if (artPrefab != null)
            {
                art = (GameObject)PrefabUtility.InstantiatePrefab(artPrefab, scene);
                art.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);   // lane coordinates = world (§7: no re-centring)
            }
            else problems.Add($"No art prefab at {artPath}: import the region art (PR #24, U-12) and run Dead Letter → Art → Build Region Prefabs. Building without set or mechanism views.");

            // Systems: the host and its adapters.
            var systems = new GameObject("SceneHost " + def.Id);
            SceneManager.MoveGameObjectToScene(systems, scene);
            var host = systems.AddComponent<SceneHost>();
            var moments = systems.AddComponent<DirectedMomentPlayer>();
            var music = systems.AddComponent<AudioDspMusicClock>();

            // D-17 at the first spawn.
            SpawnPoint spawn = def.SpawnFor(def.FirstCheckpoint);
            GameObject d17;
            var d17Asset = AssetDatabase.LoadAssetAtPath<GameObject>(D17Glb);
            if (d17Asset != null) d17 = (GameObject)PrefabUtility.InstantiatePrefab(d17Asset, scene);
            else { d17 = new GameObject(); SceneManager.MoveGameObjectToScene(d17, scene); problems.Add($"No {D17Glb}: D-17 is an empty placeholder."); }
            d17.name = "D17";
            d17.transform.SetPositionAndRotation(new Vector3((float)spawn.X, (float)spawn.Y, 0f), Quaternion.Euler(0f, spawn.Facing > 0 ? 90f : -90f, 0f));
            var animator = d17.GetComponentInChildren<Animator>();
            if (animator == null) animator = d17.AddComponent<Animator>();
            var controllerAsset = AssetDatabase.LoadAssetAtPath<AnimatorController>(D17AnimatorAsset);
            if (controllerAsset != null) animator.runtimeAnimatorController = controllerAsset;
            else problems.Add($"No {D17AnimatorAsset}: run Dead Letter → Build → D17 Animator first.");
            var player = d17.AddComponent<D17Controller>();
            var actions = AssetDatabase.LoadAssetAtPath<ScriptableObject>(InputActions);   // an InputActionAsset (the Editor asmdef has no Input System reference)
            if (actions == null) problems.Add($"No input actions at {InputActions}.");
            Set(player, "actions", actions);
            Set(player, "animator", animator);
            Transform label = FindDeep(d17.transform, "ParcelLabel") ?? FindDeep(d17.transform, "Label");   // UNVERIFIED node name (refs.label, L7652)

            // Camera: Core's rig, rendered by the driver (no Cinemachine camera yet: the driver writes the Camera).
            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            SceneManager.MoveGameObjectToScene(camGo, scene);
            var cam = camGo.AddComponent<UnityEngine.Camera>();
            cam.nearClipPlane = 0.05f;                                                     // CameraConfig.Near/Far (L7646)
            cam.farClipPlane = 60f;
            camGo.AddComponent<AudioListener>();
            var driver = camGo.AddComponent<LaneCameraDriver>();
            Set(driver, "player", player);
            Set(driver, "moments", moments);
            Set(driver, "targetCamera", cam);

            Set(moments, "player", player);
            Set(moments, "musicClock", music);
            Set(moments, "cameraDriver", driver);
            Set(host, "sceneId", def.Id);
            Set(host, "player", player);
            Set(host, "cameraDriver", driver);
            Set(host, "moments", moments);
            if (label != null) Set(host, "openingChest", label);
            else problems.Add("D-17's parcel label node was not found: the opening camera uses the definition's estimated chest.");

            // Mechanism views, one per MECH_ node, channels in definition order.
            if (art != null)
            {
                var byNode = new Dictionary<string, List<MechanismViewDef>>();
                var order = new List<string>();
                foreach (MechanismViewDef v in def.Views)
                {
                    if (!byNode.TryGetValue(v.NodeName, out var list)) { byNode[v.NodeName] = list = new List<MechanismViewDef>(); order.Add(v.NodeName); }
                    list.Add(v);
                }
                foreach (string node in order)
                {
                    Transform t = FindDeep(art.transform, node);
                    if (t == null) { problems.Add($"No art node {node} under {artPath} (a MECH_ rename missing from the export?)."); continue; }
                    var defs = byNode[node];
                    var channels = new MechanismView.Channel[defs.Count];
                    for (int i = 0; i < defs.Count; i++) channels[i] = MechanismView.From(defs[i]);
                    var view = t.gameObject.GetComponent<MechanismView>();
                    if (view == null) view = t.gameObject.AddComponent<MechanismView>();     // Unity null, not ??
                    view.Configure(host, defs[0].Node.Value, channels);
                    EditorUtility.SetDirty(view);
                    // Moved by Core: never statically batched (§6.2's StaticBatcher must skip these).
                    GameObjectUtility.SetStaticEditorFlags(t.gameObject, 0);
                }
            }

            Directory.CreateDirectory(Path.GetDirectoryName(scenePath));
            EditorSceneManager.SaveScene(scene, scenePath);
            foreach (string p in problems) Debug.LogWarning("SceneBuilder " + def.Id + ": " + p);
            Debug.Log($"SceneBuilder: built {scenePath} ({def.Views.Count} view channels, {problems.Count} warnings).");
            return problems;
        }

        private static void Set(Object target, string field, Object value)
        {
            var so = new SerializedObject(target);
            SerializedProperty p = so.FindProperty(field);
            if (p == null) { Debug.LogError($"SceneBuilder: {target.GetType().Name} has no serialized field '{field}'."); return; }
            p.objectReferenceValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void Set(Object target, string field, string value)
        {
            var so = new SerializedObject(target);
            SerializedProperty p = so.FindProperty(field);
            if (p == null) { Debug.LogError($"SceneBuilder: {target.GetType().Name} has no serialized field '{field}'."); return; }
            p.stringValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Depth-first search by name, ignoring Blender's <c>.001</c> and Unity's <c> (1)</c> suffixes (#24's ArtNames.StripDuplicateSuffix).</summary>
        private static Transform FindDeep(Transform root, string name)
        {
            if (Strip(root.name) == name) return root;
            for (int i = 0; i < root.childCount; i++)
            {
                Transform t = FindDeep(root.GetChild(i), name);
                if (t != null) return t;
            }
            return null;
        }

        private static string Strip(string n)
        {
            int open = n.LastIndexOf(" (", System.StringComparison.Ordinal);
            if (open > 0 && n.EndsWith(")")) n = n.Substring(0, open);
            if (n.Length > 4 && n[n.Length - 4] == '.' && char.IsDigit(n[n.Length - 1]) && char.IsDigit(n[n.Length - 2]) && char.IsDigit(n[n.Length - 3]))
                n = n.Substring(0, n.Length - 4);
            return n;
        }
    }
}
