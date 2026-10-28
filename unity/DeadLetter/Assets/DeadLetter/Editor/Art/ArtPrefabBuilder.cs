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
        /// <summary>The far backdrop region (tools/unity_export/conventions.py <c>BACKDROP</c>): objects over 30 m wide.</summary>
        public const string Backdrop = "DL-09_Atrium";

        /// <summary>
        /// Backdrop objects that are lane geometry, not scenery: each set region whose lane range one overlaps gets a copy,
        /// and the backdrop drops it when it overlaps none of the backdrop's scenes. Empty since #42: the export now cuts
        /// lane geometry at the region cuts (tools/unity_export/conventions.py <c>is_lane_geometry</c>), so the prologue's
        /// <c>Floor</c> arrives as one piece in each of DL-01 to DL-04. Kept as a stopgap for a future case.
        /// </summary>
        public static readonly string[] LaneSpanning = { };

        /// <summary>Used for a region with no markers to measure from (the backdrop): the last measured turn.</summary>
        private static float _lastTurnY = 180f;
        private static bool _turnMeasured;

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
            Build(names);
        }

        public static void Build(IList<string> regionNames)
        {
            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null) return;

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

            ArtIndexEntry backdrop = null;
            foreach (ArtIndexEntry e in index.regions) if (e.IsSet && e.name == Backdrop) backdrop = e;
            var cache = new Dictionary<string, Material>();
            try
            {
                for (int i = 0; i < entries.Count; i++)
                {
                    EditorUtility.DisplayProgressBar("Dead Letter: region prefabs", entries[i].name, (float)i / entries.Count);
                    BuildOne(entries[i], sidecars[entries[i].name], defs, cache, index, backdrop);
                }
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }
            AssetDatabase.SaveAssets();
        }

        private static int Count(ArtSidecar sc) => sc.markers == null ? 0 : sc.markers.Length;

        private static void BuildOne(ArtIndexEntry e, ArtSidecar sc, Dictionary<string, ArtMaterialDef> defs, Dictionary<string, Material> cache,
            ArtIndex index, ArtIndexEntry backdrop)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(e.AssetPath);
            if (source == null)
            {
                Debug.LogError("[Art] " + e.AssetPath + " has no imported GameObject (is glTFast installed and the import done?).");
                return;
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
                int lane = backdrop == null ? 0 : e == backdrop ? DropLaneSpanning(gltf, index, backdrop) : CopyLaneSpanning(e, gltf, backdrop);
                int markers = ApplyMarkers(sc, byName, out int colliders);
                int swapped = ApplyMaterials(gltf, defs, cache, out int unmatched);

                PrefabUtility.SaveAsPrefabAsset(root, e.PrefabPath, out bool ok);
                if (!ok) Debug.LogError("[Art] Could not save " + e.PrefabPath);
                else
                    Debug.Log("[Art] " + e.PrefabPath + ": " + markers + " markers (" + colliders + " colliders), " + swapped +
                              " material slots → URP Lit" + (unmatched > 0 ? ", " + unmatched + " slots kept glTFast's material" : "") +
                              (lane != 0 ? ", lane-spanning backdrop nodes " + (lane > 0 ? "copied in: " + lane : "dropped: " + -lane) : "") + ".");
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        // ---- Lane-spanning backdrop nodes --------------------------------------------------------------------------------

        /// <summary>Copies each <see cref="LaneSpanning"/> node of the backdrop that overlaps <paramref name="e"/>'s lane range. Returns the count.</summary>
        private static int CopyLaneSpanning(ArtIndexEntry e, GameObject gltf, ArtIndexEntry backdrop)
        {
            if (e.laneRange == null || e.laneRange.Length < 2) return 0;
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(backdrop.AssetPath);
            if (source == null) return 0;
            int copied = 0;
            foreach (string name in LaneSpanning)
            {
                Transform node = Find(source.transform, name);
                if (node == null) continue;
                var copy = (GameObject)Object.Instantiate(node.gameObject, gltf.transform, false);
                copy.name = name;
                copy.transform.localPosition = node.localPosition;
                copy.transform.localRotation = node.localRotation;
                copy.transform.localScale = node.localScale;
                if (Overlaps(copy, e.laneRange[0], e.laneRange[1])) copied++;
                else Object.DestroyImmediate(copy);
            }
            return copied;
        }

        /// <summary>Removes the <see cref="LaneSpanning"/> nodes that overlap none of the backdrop's own scenes. Returns minus the count.</summary>
        private static int DropLaneSpanning(GameObject gltf, ArtIndex index, ArtIndexEntry backdrop)
        {
            int dropped = 0;
            foreach (string name in LaneSpanning)
            {
                Transform node = Find(gltf.transform, name);
                if (node == null) continue;
                bool used = false;
                foreach (ArtIndexEntry r in index.regions)
                {
                    if (!r.IsSet || r == backdrop || r.laneRange == null || r.laneRange.Length < 2 || r.scenes == null) continue;
                    bool backdropScene = false;
                    foreach (string sc in r.scenes) if (System.Array.IndexOf(backdrop.scenes ?? new string[0], sc) >= 0) backdropScene = true;
                    if (backdropScene && Overlaps(node.gameObject, r.laneRange[0], r.laneRange[1])) used = true;
                }
                if (used) continue;
                Object.DestroyImmediate(node.gameObject);
                dropped++;
            }
            return -dropped;
        }

        private static Transform Find(Transform root, string name)
        {
            foreach (Transform t in root.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t;
            return null;
        }

        /// <summary>Whether the node's renderers reach into lane x [x0, x1) (world space: the prefab root sits at the origin).</summary>
        private static bool Overlaps(GameObject go, float x0, float x1)
        {
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
            {
                Bounds b = r.bounds;
                if (b.max.x > x0 && b.min.x < x1) return true;
            }
            return false;
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
                        urp = defs.TryGetValue(name, out ArtMaterialDef d) ? ArtMaterials.GetOrCreate(d) : null;
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
