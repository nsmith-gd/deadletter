using System;
using System.Collections.Generic;
using System.IO;
using DeadLetter.Core.Art;
using DeadLetter.Editor.Import;
using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Art
{
    /// <summary>
    /// Import settings for the Blender export under <c>Assets/Art/</c> (U-12; docs/unity/asset_conventions.md), re-applied
    /// on every import so nobody sets them by hand:
    /// <list type="bullet">
    /// <item><b>Textures</b> (<c>Assets/Art/Textures/*.png</c>, shared by every region): sRGB for colour, linear for data,
    /// normal maps as such (from <c>textures.json</c>), mips, NPOT kept, and per-platform caps from Core
    /// <see cref="TextureBudget"/>: PC (<c>Standalone</c>) BC7 at 2048 (murals 4096), Switch ASTC 6×6 at 1024. The
    /// sources in <c>art/</c> are never shrunk; the caps are importer settings. The Switch override goes through the
    /// platform-name string <see cref="SwitchPlatform"/> (as the audio importer does), so this compiles and runs without
    /// the Switch module.</item>
    /// <item><b>glTF / GLB</b> (except <c>Assets/Art/D17/</c>, which <see cref="D17ImportSettings"/> owns): glTFast with
    /// original node names (the conventions are in the names) and Mecanim clips (the White), set through
    /// <see cref="SerializedObject"/> because glTFast's importer class is internal (same field paths as
    /// <see cref="D17ImportSettings"/>, glTFast 6.8).</item>
    /// </list>
    /// After a region's glTF imports, <see cref="ArtPrefabBuilder"/> rebuilds that region's prefab; after textures import, the
    /// region glTFs glTFast gave up on are re-imported once (<see cref="ArtPrefabBuilder.ReimportFailedRegions"/>).
    /// </summary>
    public sealed class ArtImportSettings : AssetPostprocessor
    {
        public const string Root = "Assets/Art/";
        public const string TextureFolder = "Assets/Art/Textures/";
        public const string StandalonePlatform = "Standalone";
        public const string SwitchPlatform = "Switch";
        private const string GltfImporterType = "GLTFast.Editor.GltfImporter";

        private static Dictionary<string, ArtTextureDef> _manifest;
        private static DateTime _manifestTime;
        private static bool _warnedSwitch;

        public override uint GetVersion() => 1;

        private static bool Owned(string path) =>
            path.StartsWith(Root, StringComparison.Ordinal) && !path.StartsWith(D17ImportSettings.Folder, StringComparison.Ordinal);

        // ---- Textures ------------------------------------------------------------------------------------------------

        private void OnPreprocessTexture()
        {
            if (!Owned(assetPath)) return;
            var ti = assetImporter as TextureImporter;
            if (ti == null) return;

            ArtTextureDef def = Lookup(Path.GetFileName(assetPath));
            string use = def != null ? def.use : "color";
            TextureUse budgetUse = def != null && def.width > 0 ? TextureBudget.Classify(def.width, def.height) : TextureUse.Default;

            ti.textureType = use == "normal" ? TextureImporterType.NormalMap : TextureImporterType.Default;
            ti.sRGBTexture = use == "color";
            ti.mipmapEnabled = true;
            ti.npotScale = TextureImporterNPOTScale.None;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.filterMode = FilterMode.Trilinear;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            ti.maxTextureSize = TextureBudget.MaxSize(ArtPlatform.PC, budgetUse);

            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                name = StandalonePlatform,
                overridden = true,
                maxTextureSize = TextureBudget.MaxSize(ArtPlatform.PC, budgetUse),
                format = TextureImporterFormat.BC7,
                textureCompression = TextureImporterCompression.CompressedHQ,
            });
            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                name = SwitchPlatform,
                overridden = true,
                maxTextureSize = TextureBudget.MaxSize(ArtPlatform.Switch, budgetUse),
                format = TextureImporterFormat.ASTC_6x6,
                textureCompression = TextureImporterCompression.Compressed,
            });
            TextureImporterPlatformSettings check = ti.GetPlatformTextureSettings(SwitchPlatform);
            if ((check == null || !check.overridden) && !_warnedSwitch)
            {
                _warnedSwitch = true;
                Debug.LogWarning("[Art] The '" + SwitchPlatform + "' texture overrides did not stick (Switch module not installed): install it before importing art for Switch builds.");
            }
        }

        /// <summary>The manifest entry for a texture file, re-read when <c>textures.json</c> changes.</summary>
        public static ArtTextureDef Lookup(string fileName)
        {
            string path = ArtTextureManifest.ManifestPath;
            if (!File.Exists(path)) return null;
            DateTime t = File.GetLastWriteTimeUtc(path);
            if (_manifest == null || t != _manifestTime)
            {
                _manifest = new Dictionary<string, ArtTextureDef>(StringComparer.Ordinal);
                _manifestTime = t;
                var m = JsonUtility.FromJson<ArtTextureManifest>(File.ReadAllText(path));
                if (m != null && m.textures != null)
                    foreach (ArtTextureDef d in m.textures)
                        if (!string.IsNullOrEmpty(d.file)) _manifest[d.file] = d;
            }
            _manifest.TryGetValue(fileName, out ArtTextureDef def);
            return def;
        }

        // ---- glTF ------------------------------------------------------------------------------------------------------

        private void OnPreprocessAsset()
        {
            if (!Owned(assetPath) || !(assetPath.EndsWith(".gltf", StringComparison.Ordinal) || assetPath.EndsWith(".glb", StringComparison.Ordinal)))
                return;
            if (assetImporter == null || assetImporter.GetType().FullName != GltfImporterType)
            {
                Debug.LogWarning("[Art] " + assetPath + " is not imported by glTFast (" + assetImporter?.GetType().FullName + ").");
                return;
            }
            var so = new SerializedObject(assetImporter);
            bool ok = SetEnum(so, "importSettings.nodeNameMethod", "OriginalUnique")
                      & SetEnum(so, "importSettings.animationMethod", "Mecanim");
            SerializedProperty mips = so.FindProperty("importSettings.generateMipMaps");
            if (mips != null && !mips.boolValue) mips.boolValue = true;
            if (so.hasModifiedProperties) so.ApplyModifiedPropertiesWithoutUndo();
            if (!ok) Debug.LogWarning("[Art] glTFast import settings not found on " + assetPath + "; check node names = Original Unique.");
        }

        private static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            var regions = new List<string>();
            bool textures = false;
            foreach (string p in imported)
            {
                if (p.StartsWith(TextureFolder, StringComparison.Ordinal) && p.EndsWith(".png", StringComparison.OrdinalIgnoreCase)) textures = true;
                else if (Owned(p) && p.EndsWith(".gltf", StringComparison.Ordinal))
                    regions.Add(Path.GetFileNameWithoutExtension(p));
            }
            // glTFast fails a whole region when one of its textures is not loadable yet and never retries by itself (it only
            // depends on the textures' source files): once textures have imported, re-import the regions it gave up on.
            if (textures) EditorApplication.delayCall += () => ArtPrefabBuilder.ReimportFailedRegions();
            if (regions.Count == 0) return;
            // After the import finishes: building prefabs and materials inside an import callback is not allowed.
            EditorApplication.delayCall += () => ArtPrefabBuilder.Build(regions);
        }

        private static bool SetEnum(SerializedObject so, string path, string valueName)
        {
            SerializedProperty p = so.FindProperty(path);
            if (p == null || p.propertyType != SerializedPropertyType.Enum) return false;
            int i = Array.IndexOf(p.enumNames, valueName);
            if (i < 0) return false;
            if (p.enumValueIndex != i) p.enumValueIndex = i;
            return true;
        }
    }
}
