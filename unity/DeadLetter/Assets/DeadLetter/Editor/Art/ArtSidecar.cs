using System;
using System.IO;
using UnityEngine;

namespace DeadLetter.Editor.Art
{
    // JsonUtility-shaped mirrors of what tools/unity_export/export_regions.py writes (docs/unity/asset_conventions.md).
    // Field names match the JSON keys; unknown keys are ignored, so the Python side can add fields first.

    /// <summary><c>Assets/Art/regions.json</c>: every exported region and character.</summary>
    [Serializable]
    public sealed class ArtIndex
    {
        public const string IndexPath = "Assets/Art/regions.json";

        public int format;
        public ArtIndexEntry[] regions;

        public static ArtIndex Load()
        {
            if (!File.Exists(IndexPath)) return null;
            return JsonUtility.FromJson<ArtIndex>(File.ReadAllText(IndexPath));
        }
    }

    [Serializable]
    public sealed class ArtIndexEntry
    {
        public string name;
        /// <summary><c>set</c> (a region of the lane) or <c>character</c> (D17, White, Couriers).</summary>
        public string kind;
        public string folder;
        public string file;
        public string sidecar;
        public string[] scenes;
        public int gameRegion;
        public float[] laneRange;
        public float[] boundsMin;
        public float[] boundsMax;

        public bool IsSet => kind == "set";
        public string AssetPath => "Assets/Art/" + folder + "/" + file;
        public string SidecarPath => "Assets/Art/" + folder + "/" + sidecar;
        public string PrefabPath => "Assets/Art/" + folder + "/" + name + ".prefab";
    }

    /// <summary><c>Assets/Art/&lt;region&gt;/&lt;region&gt;.art.json</c>.</summary>
    [Serializable]
    public sealed class ArtSidecar
    {
        public int format;
        public string region;
        public string[] scenes;
        public int gameRegion;
        public float[] laneRange;
        /// <summary>Unity axes (Blender x, z, y), port_architecture §0.2.</summary>
        public float[] boundsMin;
        public float[] boundsMax;
        public string gltf;
        public ArtCounts counts;
        public ArtMarkerDef[] markers;
        public ArtMaterialDef[] materials;
        public ArtTextureDef[] textures;
        /// <summary>Source names in this region that index.html looks up by string (not yet renamed to a convention).</summary>
        public string[] driven;
        public string[] todo;

        public static ArtSidecar Load(string assetPath)
        {
            if (!File.Exists(assetPath)) return null;
            return JsonUtility.FromJson<ArtSidecar>(File.ReadAllText(assetPath));
        }
    }

    [Serializable]
    public sealed class ArtCounts
    {
        public int nodes, meshes, primitives, triangles, materials, textures;
    }

    [Serializable]
    public sealed class ArtProp
    {
        public string key;
        public string value;
    }

    [Serializable]
    public sealed class ArtMarkerDef
    {
        public string name;
        /// <summary>COL, LGT, MECH, CAM or CHK.</summary>
        public string prefix;
        public string source;
        /// <summary>The node's origin in Unity axes.</summary>
        public float[] position;
        /// <summary>Bounding-box centre in Unity axes (generators mostly build meshes in world space, origin at 0).</summary>
        public float[] center;
        public bool hasMesh;
        public ArtProp[] props;

        public Vector3 Position => position != null && position.Length == 3 ? new Vector3(position[0], position[1], position[2]) : Vector3.zero;
    }

    [Serializable]
    public sealed class ArtMaterialDef
    {
        public string name;
        /// <summary>glTF baseColorFactor, linear RGBA.</summary>
        public float[] baseColor;
        public float metallic;
        public float roughness;
        /// <summary>glTF emissiveFactor, linear RGB; multiply by <see cref="emissiveStrength"/>.</summary>
        public float[] emissive;
        public float emissiveStrength;
        public float transmission;
        /// <summary>OPAQUE, MASK or BLEND.</summary>
        public string alphaMode;
        public float alphaCutoff;
        public bool doubleSided;
        // Texture file names in Assets/Art/Textures/ (empty when unused).
        public string baseColorTexture;
        public string emissiveTexture;
        public string normalTexture;
        public float normalScale;
        public string metallicRoughnessTexture;
        public string occlusionTexture;
    }

    [Serializable]
    public sealed class ArtTextureDef
    {
        public string file;
        public int width;
        public int height;
        /// <summary>color (sRGB), normal, or linear (data).</summary>
        public string use;
    }

    /// <summary><c>Assets/Art/Textures/textures.json</c>: every shared texture, its source size and use.</summary>
    [Serializable]
    public sealed class ArtTextureManifest
    {
        public const string ManifestPath = "Assets/Art/Textures/textures.json";

        public int format;
        public ArtTextureDef[] textures;
    }
}
