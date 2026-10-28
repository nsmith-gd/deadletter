using System.Reflection;
using System.Text;
using DeadLetter.Editor.Art;
using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Diagnostics
{
    /// <summary>
    /// <c>Dead Letter → Art → Log glTF Import Reports</c>: glTFast keeps each import's errors on the importer (shown in
    /// its inspector) and logs only "Failed to import … (see inspector for details)". This writes those details to the
    /// Console, so a headless run (<c>-executeMethod DeadLetter.Editor.Diagnostics.ImportReport.LogAll</c>) shows them.
    /// </summary>
    public static class ImportReport
    {
        [MenuItem("Dead Letter/Art/Log glTF Import Reports")]
        public static void LogAll()
        {
            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null) { Debug.LogError("[Art] " + ArtIndex.IndexPath + " not found."); return; }
            foreach (ArtIndexEntry e in index.regions) Log(e.AssetPath);
        }

        /// <summary>
        /// Re-imports the shared textures, then every region and character glTF (glTFast does not declare its textures as
        /// dependencies, so a texture fix does not re-import the glTFs on its own), then logs the reports.
        /// </summary>
        [MenuItem("Dead Letter/Art/Re-import Art")]
        public static void ReimportArt()
        {
            ArtIndex index = ArtIndex.Load();
            if (index == null || index.regions == null) { Debug.LogError("[Art] " + ArtIndex.IndexPath + " not found."); return; }
            AssetDatabase.ImportAsset(ArtImportSettings.TextureFolder.TrimEnd('/'),
                ImportAssetOptions.ForceUpdate | ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceSynchronousImport);
            foreach (ArtIndexEntry e in index.regions)
                AssetDatabase.ImportAsset(e.AssetPath, ImportAssetOptions.ForceUpdate | ImportAssetOptions.ForceSynchronousImport);
            LogAll();
        }

        public static void Log(string assetPath)
        {
            AssetImporter importer = AssetImporter.GetAtPath(assetPath);
            if (importer == null) { Debug.LogWarning("[Art] " + assetPath + ": no importer."); return; }
            FieldInfo field = importer.GetType().GetField("reportItems", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            var items = field?.GetValue(importer) as System.Array;
            var sb = new StringBuilder("[Art] " + assetPath + " (" + importer.GetType().Name + "): ");
            if (items == null || items.Length == 0) { Debug.Log(sb.Append("no report items.").ToString()); return; }
            sb.Append(items.Length).Append(" report items");
            foreach (object item in items)
            {
                System.Type t = item.GetType();
                object type = t.GetProperty("Type")?.GetValue(item);
                object code = t.GetProperty("Code")?.GetValue(item);
                var messages = t.GetProperty("Messages")?.GetValue(item) as string[];
                sb.Append("\n  ").Append(type).Append(' ').Append(code);
                if (messages != null) sb.Append(": ").Append(string.Join(" | ", messages));
            }
            Debug.Log(sb.ToString());
        }
    }
}
