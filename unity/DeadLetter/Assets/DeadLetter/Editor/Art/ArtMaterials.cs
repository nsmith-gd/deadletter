using System.IO;
using DeadLetter.Core.Art;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace DeadLetter.Editor.Art
{
    /// <summary>
    /// glTF PBR materials (as the region sidecar lists them) → URP Lit material assets in <c>Assets/Art/Materials/</c>,
    /// one per Blender material name and shared by every region, so the later <c>MaterialMap</c> / worn shader (U-15,
    /// port_architecture §4.3) can key on the same names the web build does. Textures are the shared
    /// <c>Assets/Art/Textures/</c> PNGs, whose importer carries the per-platform caps.
    /// <list type="bullet">
    /// <item>Base colour factor and map, metallic, smoothness = 1 − roughness.</item>
    /// <item>Emission = emissiveFactor × KHR_materials_emissive_strength (HDR), with its map; <c>_EMISSION</c> on and
    /// realtime-emissive GI flags (no lightmaps in this game, §8.2), so <c>EmissiveDriver</c> can scale it later.</item>
    /// <item>alphaMode BLEND → URP transparent (alpha blend), MASK → alpha clip, OPAQUE → opaque; doubleSided → cull off.</item>
    /// <item>Normal map with its scale. Not converted (none exist in the export today; warned if they appear):
    /// metallicRoughness maps (glTF packs metal in B and roughness in G, URP wants metal R and smoothness A) and
    /// occlusion (glTF R, URP G). KHR_materials_transmission has no URP Lit equivalent (2 materials; the web build
    /// replaces them by name with its GLASSY table, as U-15's MaterialMap will).</item>
    /// </list>
    /// Colours are glTF linear values; a material colour in Unity is stored gamma-encoded and linearised for the shader
    /// in a Linear project, hence <c>.gamma</c> on the way in.
    /// <para><b>The prototype's tables come first</b> (Core <see cref="PrototypeMaterials"/>, index.html L393–L554): for a
    /// name in <c>WORN</c>, <c>PLAIN</c>, <c>GLASSY</c> or <c>EMIT</c> the web build ignores the exported material (most are
    /// white placeholders) and builds its own, and so does this: <c>WORN</c> → the <c>DeadLetter/Worn</c> shader (URP Lit
    /// plus the prototype's grime, chips and dust), the others → URP Lit with the table's values; an image keeps its map at
    /// roughness 0.75 (decals blend). Names in no table keep the glTF values as above.</para>
    /// </summary>
    public static class ArtMaterials
    {
        public const string Folder = "Assets/Art/Materials";
        public const string LitShaderName = "Universal Render Pipeline/Lit";
        public const string WornShaderName = "DeadLetter/Worn";
        public const string UnlitShaderName = "Universal Render Pipeline/Unlit";

        private static readonly int WornDirt = Shader.PropertyToID("_WornDirt");
        private static readonly int WornChip = Shader.PropertyToID("_WornChip");
        private static readonly int WornDust = Shader.PropertyToID("_WornDust");
        private static readonly int WornParams = Shader.PropertyToID("_WornParams");
        private static readonly int WornParams2 = Shader.PropertyToID("_WornParams2");

        private static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        private static readonly int BaseMap = Shader.PropertyToID("_BaseMap");
        private static readonly int Metallic = Shader.PropertyToID("_Metallic");
        private static readonly int Smoothness = Shader.PropertyToID("_Smoothness");
        private static readonly int BumpMap = Shader.PropertyToID("_BumpMap");
        private static readonly int BumpScale = Shader.PropertyToID("_BumpScale");
        private static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");
        private static readonly int EmissionMap = Shader.PropertyToID("_EmissionMap");
        private static readonly int Surface = Shader.PropertyToID("_Surface");
        private static readonly int Blend = Shader.PropertyToID("_Blend");
        private static readonly int AlphaClip = Shader.PropertyToID("_AlphaClip");
        private static readonly int Cutoff = Shader.PropertyToID("_Cutoff");
        private static readonly int Cull = Shader.PropertyToID("_Cull");
        private static readonly int SrcBlend = Shader.PropertyToID("_SrcBlend");
        private static readonly int DstBlend = Shader.PropertyToID("_DstBlend");
        private static readonly int SrcBlendAlpha = Shader.PropertyToID("_SrcBlendAlpha");
        private static readonly int DstBlendAlpha = Shader.PropertyToID("_DstBlendAlpha");
        private static readonly int ZWrite = Shader.PropertyToID("_ZWrite");

        public static string PathFor(string materialName) => Folder + "/" + FileSafe(materialName) + ".mat";

        /// <summary>Creates or updates the URP Lit material for <paramref name="d"/>; null if URP Lit is missing.</summary>
        public static Material GetOrCreate(ArtMaterialDef d)
        {
            MaterialSpec spec = SpecFor(d);
            string shaderName = spec.Kind == MaterialKind.Worn ? WornShaderName : spec.Kind == MaterialKind.Additive ? UnlitShaderName : LitShaderName;
            Shader lit = Shader.Find(shaderName);
            if (lit == null)
            {
                Debug.LogError("[Art] Shader '" + shaderName + "' not found. Is URP the active render pipeline?");
                return null;
            }
            if (!AssetDatabase.IsValidFolder(Folder)) AssetDatabase.CreateFolder("Assets/Art", "Materials");
            string path = PathFor(d.name);
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool create = mat == null;
            if (create) mat = new Material(lit);
            else if (mat.shader != lit) mat.shader = lit;
            mat.name = Path.GetFileNameWithoutExtension(path);
            if (spec.Kind == MaterialKind.Source) Apply(mat, d);
            else Apply(mat, d, spec);
            if (create) AssetDatabase.CreateAsset(mat, path);
            else EditorUtility.SetDirty(mat);
            return mat;
        }

        public static void Apply(Material m, ArtMaterialDef d)
        {
            Color baseLinear = d.baseColor != null && d.baseColor.Length >= 4
                ? new Color(d.baseColor[0], d.baseColor[1], d.baseColor[2], d.baseColor[3]) : Color.white;
            m.SetColor(BaseColor, baseLinear.gamma);
            m.SetTexture(BaseMap, LoadTexture(d.baseColorTexture));
            m.SetFloat(Metallic, Mathf.Clamp01(d.metallic));
            m.SetFloat(Smoothness, 1f - Mathf.Clamp01(d.roughness));

            Texture2D normal = LoadTexture(d.normalTexture);
            m.SetTexture(BumpMap, normal);
            m.SetFloat(BumpScale, d.normalScale > 0 ? d.normalScale : 1f);
            SetKeyword(m, "_NORMALMAP", normal != null);
            if (!string.IsNullOrEmpty(d.metallicRoughnessTexture) || !string.IsNullOrEmpty(d.occlusionTexture))
                Debug.LogWarning("[Art] " + d.name + ": metallicRoughness/occlusion maps are not converted to URP Lit yet (see ArtMaterials).");

            // Emission (HDR).
            float k = d.emissiveStrength > 0 ? d.emissiveStrength : 1f;
            Color e = d.emissive != null && d.emissive.Length >= 3 ? new Color(d.emissive[0] * k, d.emissive[1] * k, d.emissive[2] * k, 1f) : Color.black;
            Texture2D emissionMap = LoadTexture(d.emissiveTexture);
            bool emits = e.maxColorComponent > 0f || emissionMap != null;
            if (emissionMap != null && e.maxColorComponent <= 0f) e = Color.white;
            m.SetColor(EmissionColor, emits ? e.gamma : Color.black);
            m.SetTexture(EmissionMap, emissionMap);
            SetKeyword(m, "_EMISSION", emits);
            m.globalIlluminationFlags = emits ? MaterialGlobalIlluminationFlags.RealtimeEmissive : MaterialGlobalIlluminationFlags.EmissiveIsBlack;

            // Faces.
            m.SetFloat(Cull, d.doubleSided ? (float)CullMode.Off : (float)CullMode.Back);
            m.doubleSidedGI = d.doubleSided;

            // Surface.
            string mode = string.IsNullOrEmpty(d.alphaMode) ? "OPAQUE" : d.alphaMode;
            if (mode == "BLEND")
            {
                m.SetFloat(Surface, 1f);
                m.SetFloat(Blend, 0f);   // Alpha
                m.SetFloat(AlphaClip, 0f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetFloat(SrcBlend, (float)BlendMode.SrcAlpha);
                m.SetFloat(DstBlend, (float)BlendMode.OneMinusSrcAlpha);
                m.SetFloat(SrcBlendAlpha, (float)BlendMode.One);
                m.SetFloat(DstBlendAlpha, (float)BlendMode.OneMinusSrcAlpha);
                m.SetFloat(ZWrite, 0f);
                SetKeyword(m, "_SURFACE_TYPE_TRANSPARENT", true);
                SetKeyword(m, "_ALPHATEST_ON", false);
                m.SetShaderPassEnabled("DepthOnly", false);
                m.renderQueue = (int)RenderQueue.Transparent;
            }
            else
            {
                bool clip = mode == "MASK";
                m.SetFloat(Surface, 0f);
                m.SetFloat(AlphaClip, clip ? 1f : 0f);
                m.SetFloat(Cutoff, d.alphaCutoff > 0 ? d.alphaCutoff : 0.5f);
                m.SetOverrideTag("RenderType", clip ? "TransparentCutout" : "Opaque");
                m.SetFloat(SrcBlend, (float)BlendMode.One);
                m.SetFloat(DstBlend, (float)BlendMode.Zero);
                m.SetFloat(SrcBlendAlpha, (float)BlendMode.One);
                m.SetFloat(DstBlendAlpha, (float)BlendMode.Zero);
                m.SetFloat(ZWrite, 1f);
                SetKeyword(m, "_SURFACE_TYPE_TRANSPARENT", false);
                SetKeyword(m, "_ALPHATEST_ON", clip);
                m.SetShaderPassEnabled("DepthOnly", true);
                m.renderQueue = clip ? (int)RenderQueue.AlphaTest : (int)RenderQueue.Geometry;
            }
        }

        /// <summary>
        /// The prototype's material for an imported one that has no sidecar entry (the characters' GLBs: D-17's
        /// <c>CreamPaint.003</c> → <c>CreamPaint.mat</c>, shared with the sets). Null when the tables don't list the name or
        /// it is an image (the import keeps its embedded map). An existing asset is reused as it is, so a set's sidecar
        /// settings (double-sided) are not overwritten by a character's.
        /// </summary>
        public static Material ForSource(Material source)
        {
            if (source == null) return null;
            MaterialSpec spec = PrototypeMaterials.For(source.name);
            if (spec.Kind == MaterialKind.Source || spec.Kind == MaterialKind.Image) return null;
            var existing = AssetDatabase.LoadAssetAtPath<Material>(PathFor(spec.Name));
            if (existing != null) return existing;
            return GetOrCreate(new ArtMaterialDef { name = spec.Name, alphaMode = "OPAQUE" });
        }

        /// <summary>Swaps every renderer's materials under <paramref name="root"/> for the prototype's (<see cref="ForSource"/>). Returns the slots swapped.</summary>
        public static int ApplyToHierarchy(GameObject root)
        {
            int swapped = 0;
            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    Material m = ForSource(mats[i]);
                    if (m == null) continue;
                    mats[i] = m;
                    changed = true;
                    swapped++;
                }
                if (changed) r.sharedMaterials = mats;
            }
            return swapped;
        }

        /// <summary>What the prototype makes of this exported material (<see cref="PrototypeMaterials.For"/>).</summary>
        public static MaterialSpec SpecFor(ArtMaterialDef d) =>
            PrototypeMaterials.For(d.name, hasImage: !string.IsNullOrEmpty(d.baseColorTexture), sourceTransparent: d.alphaMode == "BLEND");

        /// <summary>A material from the prototype's tables (<c>materialFor</c>, L527–L554).</summary>
        public static void Apply(Material m, ArtMaterialDef d, MaterialSpec spec)
        {
            Color baseLinear = ToColor(spec.Color, (float)spec.Opacity);
            m.SetColor(BaseColor, baseLinear.gamma);
            m.SetTexture(BaseMap, spec.Kind == MaterialKind.Image ? LoadTexture(d.baseColorTexture) : null);
            m.SetFloat(Metallic, Mathf.Clamp01((float)spec.Metalness));
            m.SetFloat(Smoothness, 1f - Mathf.Clamp01((float)spec.Roughness));
            m.SetTexture(BumpMap, null);
            SetKeyword(m, "_NORMALMAP", false);

            if (spec.Kind == MaterialKind.Worn)
            {
                WornSpec w = spec.Worn;
                m.SetVector(WornDirt, ToVector(w.Dirt));
                m.SetVector(WornChip, ToVector(w.Chip));
                m.SetVector(WornDust, ToVector(w.Dust));
                m.SetVector(WornParams, new Vector4((float)w.Grime, (float)w.ChipScale, (float)w.ChipAmt, (float)w.ChipRough));
                m.SetVector(WornParams2, new Vector4((float)w.DustAmt, (float)w.Streak, 0f, 0f));
            }

            // Emission: EMIT names start at the table's intensity (most are 0: the game lights them by name).
            bool emits = spec.Kind == MaterialKind.Emit;
            Color e = emits ? ToColor(spec.Emissive, 1f) * (float)spec.EmissiveIntensity : Color.black;
            e.a = 1f;
            m.SetColor(EmissionColor, emits ? e.gamma : Color.black);
            m.SetTexture(EmissionMap, null);
            SetKeyword(m, "_EMISSION", emits);
            m.globalIlluminationFlags = emits ? MaterialGlobalIlluminationFlags.RealtimeEmissive : MaterialGlobalIlluminationFlags.EmissiveIsBlack;

            bool doubleSided = d.doubleSided || spec.Kind == MaterialKind.Additive;
            m.SetFloat(Cull, doubleSided ? (float)CullMode.Off : (float)CullMode.Back);
            m.doubleSidedGI = doubleSided;

            if (spec.Kind == MaterialKind.Additive) SetTransparent(m, additive: true, clip: false, cutoff: 0f);
            else if (spec.Transparent) SetTransparent(m, additive: false, clip: spec.AlphaTest > 0, cutoff: (float)spec.AlphaTest);
            else SetOpaque(m);
        }

        private static void SetTransparent(Material m, bool additive, bool clip, float cutoff)
        {
            m.SetFloat(Surface, 1f);
            m.SetFloat(Blend, additive ? 2f : 0f);   // URP BlendMode: Additive or Alpha
            m.SetFloat(AlphaClip, clip ? 1f : 0f);
            m.SetFloat(Cutoff, cutoff);
            m.SetOverrideTag("RenderType", "Transparent");
            m.SetFloat(SrcBlend, additive ? (float)BlendMode.One : (float)BlendMode.SrcAlpha);
            m.SetFloat(DstBlend, additive ? (float)BlendMode.One : (float)BlendMode.OneMinusSrcAlpha);
            m.SetFloat(SrcBlendAlpha, (float)BlendMode.One);
            m.SetFloat(DstBlendAlpha, (float)BlendMode.OneMinusSrcAlpha);
            m.SetFloat(ZWrite, 0f);
            SetKeyword(m, "_SURFACE_TYPE_TRANSPARENT", true);
            SetKeyword(m, "_ALPHATEST_ON", clip);
            m.SetShaderPassEnabled("DepthOnly", false);
            m.renderQueue = (int)RenderQueue.Transparent;
        }

        private static void SetOpaque(Material m)
        {
            m.SetFloat(Surface, 0f);
            m.SetFloat(AlphaClip, 0f);
            m.SetFloat(Cutoff, 0.5f);
            m.SetOverrideTag("RenderType", "Opaque");
            m.SetFloat(SrcBlend, (float)BlendMode.One);
            m.SetFloat(DstBlend, (float)BlendMode.Zero);
            m.SetFloat(SrcBlendAlpha, (float)BlendMode.One);
            m.SetFloat(DstBlendAlpha, (float)BlendMode.Zero);
            m.SetFloat(ZWrite, 1f);
            SetKeyword(m, "_SURFACE_TYPE_TRANSPARENT", false);
            SetKeyword(m, "_ALPHATEST_ON", false);
            m.SetShaderPassEnabled("DepthOnly", true);
            m.renderQueue = (int)RenderQueue.Geometry;
        }

        private static Color ToColor(Rgb c, float a) => new Color((float)c.R, (float)c.G, (float)c.B, a);
        private static Vector4 ToVector(Rgb c) => new Vector4((float)c.R, (float)c.G, (float)c.B, 1f);

        private static Texture2D LoadTexture(string file)
        {
            if (string.IsNullOrEmpty(file)) return null;
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(ArtImportSettings.TextureFolder + file);
            if (t == null) Debug.LogWarning("[Art] Texture " + ArtImportSettings.TextureFolder + file + " not found (re-run the export?).");
            return t;
        }

        private static void SetKeyword(Material m, string keyword, bool on)
        {
            if (on) m.EnableKeyword(keyword);
            else m.DisableKeyword(keyword);
        }

        /// <summary>A Blender material name as a file name (Blender allows characters Windows paths do not).</summary>
        public static string FileSafe(string name)
        {
            if (string.IsNullOrEmpty(name)) return "_unnamed";
            char[] bad = Path.GetInvalidFileNameChars();
            var c = name.ToCharArray();
            for (int i = 0; i < c.Length; i++)
                if (System.Array.IndexOf(bad, c[i]) >= 0 || c[i] == '/' || c[i] == '\\' || c[i] == ':' || c[i] == '*' || c[i] == '?' || c[i] == '"' || c[i] == '<' || c[i] == '>' || c[i] == '|')
                    c[i] = '_';
            return new string(c);
        }
    }
}
