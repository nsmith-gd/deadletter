using System.Collections.Generic;
using DeadLetter.Core.Art;
using DeadLetter.Runtime.Art;
using ArtMarker = DeadLetter.Runtime.Art.ArtMarker;
using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Art
{
    /// <summary>
    /// <c>Dead Letter → Art → Build Region Prefabs</c> (U-12; docs/unity/asset_conventions.md). For every region in
    /// <c>Assets/Art/regions.json</c> it takes glTFast's imported hierarchy of <c>&lt;region&gt;.gltf</c> and writes
    /// <c>Assets/Art/&lt;region&gt;/&lt;region&gt;.prefab</c>, applying the conventions on that copy (the imported asset is
    /// never edited, so this is safe to re-run and needs no glTFast import hooks):
    /// <list type="number">
    /// <item><b>Axes.</b> The prefab root holds the glTF hierarchy under a child turned about Y so that world positions
    /// match port_architecture §0.2 (Unity = Blender x, z, y). The turn (0° or 180°) is measured, not assumed: the
    /// sidecar's markers carry their expected positions, and the builder picks the turn that puts them there (and warns
    /// if neither does). This is the §0.2 handedness check, re-run on every build.</item>
    /// <item><b>COL_</b> nodes get a <see cref="BoxCollider"/> fitted to their mesh, and lose the renderer.</item>
    /// <item><b>COL_/LGT_/MECH_/CAM_/CHK_</b> nodes get an <see cref="ArtMarker"/> with the sidecar's data; empties stay
    /// as empty transforms for the scene builder.</item>
    /// <item><b>Materials</b> are swapped, by glTF material name, for the URP Lit assets of <see cref="ArtMaterials"/>.</item>
    /// </list>
    /// Runs on its own after a region's glTF (re)imports (<see cref="ArtImportSettings"/>). Static batching flags,
    /// LODs and shadow-caster rules are the scene builder's (U-20), which knows which objects mechanisms move.
    /// </summary>
    public static class ArtPrefabBuilder
    {
        /// <summary>Used for a region with no markers to measure from (the backdrop): the last measured turn.</summary>
        private static float _lastTurnY = 180f;
        private static bool _turnMeasured;
        /// <summary>glTFs already force-reimported once this session because they had no GameObject (no reimport loop).</summary>
        private static readonly HashSet<string> _reimported = new HashSet<string>();

        [MenuItem("Dead Letter/Art/Build Region Prefabs")]
        public static void BuildAll()
        {
            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null)
            {
                Debug.LogError("[Art] " + ArtIndex.IndexPath + " not found. Run tools/unity_export/export_regions.py first.");
                return;
            }
            var names = new List<string>();
            foreach (ArtIndexEntry e in index.regions) if (e.IsSet) names.Add(e.name);
            if (names.Count == 0)
            {
                Debug.LogError("[Art] " + ArtIndex.IndexPath + " lists " + index.regions.Length + " entries but none with kind \"set\": no region prefab to build.");
                return;
            }
            int built = Build(names);
            if (built == 0)
                EditorUtility.DisplayDialog("Dead Letter: region prefabs", "No region prefab was built. The Console says why for each region " +
                                            "(usually: glTFast failed to import the .gltf; select it and read its Inspector).", "OK");
        }

        /// <summary>Builds the named regions' prefabs; returns how many were written. Always logs a summary.</summary>
        public static int Build(IList<string> regionNames)
        {
            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null)
            {
                Debug.LogError("[Art] " + ArtIndex.IndexPath + " not found or unreadable (cwd " + System.IO.Directory.GetCurrentDirectory() + "): no region prefab built.");
                return 0;
            }

            // Material definitions from every sidecar (one Blender material can appear in several regions).
            var defs = new Dictionary<string, ArtMaterialDef>();
            var sidecars = new Dictionary<string, ArtSidecar>();
            var entries = new List<ArtIndexEntry>();
            foreach (ArtIndexEntry e in index.regions)
            {
                if (!e.IsSet) continue;
                ArtSidecar sc = ArtSidecar.Load(e.SidecarPath);
                if (sc == null) { Debug.LogError("[Art] Missing sidecar " + e.SidecarPath); continue; }
                sidecars[e.name] = sc;
                if (sc.materials != null)
                    foreach (ArtMaterialDef d in sc.materials)
                        if (!defs.ContainsKey(d.name)) defs[d.name] = d;
                if (regionNames.Contains(e.name)) entries.Add(e);
            }
            // Regions with markers first, so the backdrop reuses a measured turn.
            entries.Sort((a, b) => Count(sidecars[b.name]).CompareTo(Count(sidecars[a.name])));

            var cache = new Dictionary<string, Material>();
            var failed = new List<string>();
            int built = 0;
            try
            {
                for (int i = 0; i < entries.Count; i++)
                {
                    EditorUtility.DisplayProgressBar("Dead Letter: region prefabs", entries[i].name, (float)i / entries.Count);
                    if (BuildOne(entries[i], sidecars[entries[i].name], defs, cache)) built++;
                    else failed.Add(entries[i].name);
                }
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }
            AssetDatabase.SaveAssets();
            string summary = "[Art] Region prefabs: " + built + " of " + regionNames.Count + " requested built" +
                             (failed.Count > 0 ? "; FAILED: " + string.Join(", ", failed) : "") +
                             (entries.Count < regionNames.Count ? "; " + (regionNames.Count - entries.Count) + " not in " + ArtIndex.IndexPath + " as a set with a sidecar" : "") + ".";
            if (built == 0 || failed.Count > 0) Debug.LogError(summary);
            else Debug.Log(summary);
            return built;
        }

        private static int Count(ArtSidecar sc) => sc.markers == null ? 0 : sc.markers.Length;

        private static bool BuildOne(ArtIndexEntry e, ArtSidecar sc, Dictionary<string, ArtMaterialDef> defs, Dictionary<string, Material> cache)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(e.AssetPath);
            if (source == null && System.IO.File.Exists(e.AssetPath) && _reimported.Add(e.AssetPath))
            {
                // glTFast aborts the whole import when one external texture is not loadable yet (GltfImport.WaitForTextureDownloads
                // returns false on the first TextureDownloadFailed), which happens when the .gltf imports before or alongside
                // Assets/Art/Textures/. It only declares DependsOnSourceAsset on them, so nothing re-imports it later. Once, now.
                Debug.LogWarning("[Art] " + e.AssetPath + " has no imported GameObject (" + GltfImportReport(e.AssetPath) + "); re-importing it once.");
                AssetDatabase.ImportAsset(e.AssetPath, ImportAssetOptions.ForceUpdate | ImportAssetOptions.ForceSynchronousImport);
                source = AssetDatabase.LoadAssetAtPath<GameObject>(e.AssetPath);
            }
            if (source == null)
            {
                Debug.LogError("[Art] " + e.AssetPath + " has no imported GameObject: " + GltfImportReport(e.AssetPath) +
                               ". Select it and read glTFast's report in the Inspector; Reimport it once Assets/Art/Textures/ has imported.");
                return false;
            }
            var root = new GameObject(e.name);
            var gltf = (GameObject)Object.Instantiate(source);
            gltf.name = e.name + "_gltf";
            gltf.transform.SetParent(root.transform, false);
            try
            {
                var byName = new Dictionary<string, Transform>();
                foreach (Transform t in gltf.GetComponentsInChildren<Transform>(true))
                    if (!byName.ContainsKey(t.name)) byName[t.name] = t;

                gltf.transform.localRotation = Quaternion.Euler(0f, MeasureTurn(e.name, sc, byName), 0f);
                int markers = ApplyMarkers(sc, byName, out int colliders);
                int swapped = ApplyMaterials(gltf, defs, cache, out int unmatched);

                PrefabUtility.SaveAsPrefabAsset(root, e.PrefabPath, out bool ok);
                if (!ok) Debug.LogError("[Art] Could not save " + e.PrefabPath);
                else
                    Debug.Log("[Art] " + e.PrefabPath + ": " + markers + " markers (" + colliders + " colliders), " + swapped +
                              " material slots → URP Lit" + (unmatched > 0 ? ", " + unmatched + " slots kept glTFast's material" : "") + ".");
                return ok;
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        /// <summary>
        /// Re-imports, once per session, every region glTF that has no GameObject (glTFast gave up on it, usually because a
        /// shared texture was not loadable yet). Their re-import rebuilds their prefabs (<see cref="ArtImportSettings"/>).
        /// Returns how many were queued.
        /// </summary>
        public static int ReimportFailedRegions()
        {
            ArtIndex index = ArtIndex.Load();
            if (index?.regions == null) return 0;
            var paths = new List<string>();
            foreach (ArtIndexEntry e in index.regions)
                if (e.IsSet && System.IO.File.Exists(e.AssetPath) && AssetDatabase.LoadAssetAtPath<GameObject>(e.AssetPath) == null && _reimported.Add(e.AssetPath))
                    paths.Add(e.AssetPath);
            if (paths.Count == 0) return 0;
            Debug.LogWarning("[Art] " + paths.Count + " region glTF(s) have no imported GameObject (" + GltfImportReport(paths[0]) +
                             "); re-importing them now that the textures are in: " + string.Join(", ", paths));
            AssetDatabase.StartAssetEditing();
            try { foreach (string p in paths) AssetDatabase.ImportAsset(p, ImportAssetOptions.ForceUpdate); }
            finally { AssetDatabase.StopAssetEditing(); }
            return paths.Count;
        }

        /// <summary>glTFast's own import report for <paramref name="assetPath"/> (its importer's serialized <c>reportItems</c>): the errors, else "no report".</summary>
        public static string GltfImportReport(string assetPath)
        {
            AssetImporter importer = AssetImporter.GetAtPath(assetPath);
            if (importer == null) return "no importer (is the file in the project?)";
            if (importer.GetType().FullName != "GLTFast.Editor.GltfImporter") return "imported by " + importer.GetType().FullName + ", not glTFast";
            SerializedProperty items = new SerializedObject(importer).FindProperty("reportItems");
            if (items == null || !items.isArray || items.arraySize == 0) return "glTFast reported nothing";
            var errors = new List<string>();
            for (int i = 0; i < items.arraySize; i++)
            {
                SerializedProperty it = items.GetArrayElementAtIndex(i);
                SerializedProperty type = it.FindPropertyRelative("type");
                if (type == null || (type.intValue != (int)LogType.Error && type.intValue != (int)LogType.Exception)) continue;
                SerializedProperty msgs = it.FindPropertyRelative("messages");
                string text = msgs != null && msgs.isArray && msgs.arraySize > 0 ? msgs.GetArrayElementAtIndex(0).stringValue : "";
                SerializedProperty code = it.FindPropertyRelative("code");
                errors.Add("glTFast error " + (code != null ? code.intValue.ToString() : "?") + (text.Length > 0 ? ": " + text : ""));
            }
            return errors.Count > 0 ? string.Join("; ", errors) : "glTFast reported no error";
        }

        // ---- Axes ------------------------------------------------------------------------------------------------------

        /// <summary>0 or 180: whichever puts the sidecar's markers where §0.2 says they are.</summary>
        private static float MeasureTurn(string region, ArtSidecar sc, Dictionary<string, Transform> byName)
        {
            double err0 = 0, err180 = 0;
            int n = 0;
            Quaternion turn = Quaternion.Euler(0f, 180f, 0f);
            if (sc.markers != null)
                foreach (ArtMarkerDef m in sc.markers)
                {
                    if (m.position == null || m.position.Length != 3 || !byName.TryGetValue(m.name, out Transform t)) continue;
                    Vector3 p = t.position;   // the glTF root sits at the origin, unturned, at this point
                    err0 += (p - m.Position).magnitude;
                    err180 += (turn * p - m.Position).magnitude;
                    n++;
                }
            if (n == 0)
            {
                if (!_turnMeasured)
                    Debug.Log("[Art] " + region + ": no markers to measure the glTF axes from; using " + _lastTurnY + "° about Y.");
                return _lastTurnY;
            }
            float best = err180 < err0 ? 180f : 0f;
            double mean = System.Math.Min(err0, err180) / n;
            if (mean > 0.01)
                Debug.LogWarning("[Art] " + region + ": markers are " + mean.ToString("0.###") + " m from their sidecar positions on average " +
                                 "after the best turn (0°: " + (err0 / n).ToString("0.###") + ", 180°: " + (err180 / n).ToString("0.###") +
                                 "). glTFast's axis conversion is not the one §0.2 expects; check one marker by hand.");
            _lastTurnY = best;
            _turnMeasured = true;
            return best;
        }

        // ---- Markers and colliders -------------------------------------------------------------------------------------

        private static int ApplyMarkers(ArtSidecar sc, Dictionary<string, Transform> byName, out int colliders)
        {
            colliders = 0;
            var defs = new Dictionary<string, ArtMarkerDef>();
            if (sc.markers != null) foreach (ArtMarkerDef m in sc.markers) defs[m.name] = m;
            int count = 0;
            foreach (KeyValuePair<string, Transform> kv in byName)
            {
                ArtName n = ArtNames.Parse(kv.Key);
                if (!n.IsMarker) continue;
                Transform t = kv.Value;
                if (n.Prefix == ArtPrefix.Collider && MakeCollider(t)) colliders++;
                var marker = t.GetComponent<ArtMarker>();   // no ?? on UnityEngine.Object (fake null)
                if (marker == null) marker = t.gameObject.AddComponent<ArtMarker>();
                marker.prefix = ArtNames.PrefixOf(n.Prefix).TrimEnd('_');
                marker.type = n.Type ?? "";
                marker.id = n.Id ?? "";
                marker.part = n.Part ?? "";
                marker.props.Clear();
                if (defs.TryGetValue(kv.Key, out ArtMarkerDef d))
                {
                    marker.sourceName = d.source ?? "";
                    if (d.props != null)
                        foreach (ArtProp p in d.props) marker.props.Add(new ArtMarker.Prop { key = p.key, value = p.value });
                }
                count++;
            }
            return count;
        }

        /// <summary>A box fitted to the node's meshes (in its own space); the renderers and mesh filters go.</summary>
        private static bool MakeCollider(Transform t)
        {
            var filters = t.GetComponentsInChildren<MeshFilter>(true);
            bool any = false;
            var b = new Bounds();
            foreach (MeshFilter f in filters)
            {
                if (f.sharedMesh == null) continue;
                Bounds mb = f.sharedMesh.bounds;
                Matrix4x4 m = t.worldToLocalMatrix * f.transform.localToWorldMatrix;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = mb.center + Vector3.Scale(mb.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    Vector3 p = m.MultiplyPoint3x4(c);
                    if (!any) { b = new Bounds(p, Vector3.zero); any = true; }
                    else b.Encapsulate(p);
                }
            }
            if (!any)
            {
                Debug.LogWarning("[Art] " + t.name + " has no mesh to size a collider from; it stays an empty marker.");
                return false;
            }
            var box = t.GetComponent<BoxCollider>();
            if (box == null) box = t.gameObject.AddComponent<BoxCollider>();
            box.center = b.center;
            box.size = b.size;
            foreach (Renderer r in t.GetComponentsInChildren<Renderer>(true)) Object.DestroyImmediate(r);
            foreach (MeshFilter f in filters) Object.DestroyImmediate(f);
            return true;
        }

        // ---- Materials -------------------------------------------------------------------------------------------------

        private static int ApplyMaterials(GameObject gltf, Dictionary<string, ArtMaterialDef> defs, Dictionary<string, Material> cache, out int unmatched)
        {
            int swapped = 0;
            unmatched = 0;
            foreach (Renderer r in gltf.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    string name = mats[i].name;
                    if (!cache.TryGetValue(name, out Material urp))
                    {
                        if (defs.TryGetValue(name, out ArtMaterialDef d)) urp = ArtMaterials.GetOrCreate(d);
                        else if (PrototypeMaterials.Lookup(name, out _)) urp = ArtMaterials.GetOrCreate(new ArtMaterialDef { name = PrototypeMaterials.BaseName(name) });
                        else urp = null;
                        cache[name] = urp;
                    }
                    if (urp == null) { unmatched++; continue; }
                    mats[i] = urp;
                    changed = true;
                    swapped++;
                }
                if (changed) r.sharedMaterials = mats;
            }
            return swapped;
        }
    }
}
