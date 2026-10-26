using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Import
{
    /// <summary>
    /// Pins glTFast's import settings for D-17 (<c>Assets/Art/D17/*.glb</c>) so the clips come in as Mecanim (generic,
    /// non-legacy) clips with an <see cref="Animator"/> on the imported root.
    /// <para>
    /// glTFast 6.8's <c>GltfImporter</c> already defaults a fresh editor import to Mecanim + <c>OriginalUnique</c> node
    /// names + mipmaps, but only while its <c>importSettings</c> field is still null; a hand-edited or partly serialized
    /// .meta can bring back the runtime defaults (Legacy clips, which an Animator cannot play). This postprocessor
    /// re-applies the editor defaults on every import. The importer class is internal to glTFast, so it is reached
    /// through <see cref="SerializedObject"/> by field name (glTFast 6.8: <c>importSettings.animationMethod</c>,
    /// <c>importSettings.nodeNameMethod</c>, <c>importSettings.generateMipMaps</c>).
    /// </para>
    /// <para>
    /// glTFast sets <c>loopTime = true</c> on every Mecanim clip and has no per-clip setting. The one-shot clips are held
    /// on their last frame by the controller instead (see <see cref="Builders.D17AnimatorBuilder"/>).
    /// </para>
    /// </summary>
    public class D17ImportSettings : AssetPostprocessor
    {
        public const string Folder = "Assets/Art/D17/";
        private const string GltfImporterType = "GLTFast.Editor.GltfImporter";

        public override uint GetVersion() => 1;

        private void OnPreprocessAsset()
        {
            if (!assetPath.StartsWith(Folder) || !assetPath.EndsWith(".glb")) return;
            if (assetImporter == null || assetImporter.GetType().FullName != GltfImporterType)
            {
                Debug.LogWarning($"[D17] {assetPath} is not imported by glTFast ({assetImporter?.GetType().FullName}); " +
                                 "the D17 Animator expects glTFast Mecanim clips.");
                return;
            }

            var so = new SerializedObject(assetImporter);
            bool ok = SetEnum(so, "importSettings.animationMethod", "Mecanim")
                    & SetEnum(so, "importSettings.nodeNameMethod", "OriginalUnique");
            var mips = so.FindProperty("importSettings.generateMipMaps");
            if (mips != null && !mips.boolValue) mips.boolValue = true;
            if (so.hasModifiedProperties) so.ApplyModifiedPropertiesWithoutUndo();
            if (!ok)
                Debug.LogWarning($"[D17] glTFast import settings not found on {assetPath}; check Inspector → Animation = Mecanim.");
        }

        private static bool SetEnum(SerializedObject so, string path, string valueName)
        {
            var p = so.FindProperty(path);
            if (p == null || p.propertyType != SerializedPropertyType.Enum) return false;
            int i = System.Array.IndexOf(p.enumNames, valueName);
            if (i < 0) return false;
            if (p.enumValueIndex != i) p.enumValueIndex = i;
            return true;
        }
    }
}
