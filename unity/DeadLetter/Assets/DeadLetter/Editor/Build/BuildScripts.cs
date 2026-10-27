using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace DeadLetter.Editor.Build
{
    /// <summary>
    /// Command-line player builds (task U-17). Every desktop build is IL2CPP; the Steam variants add the
    /// <c>DL_STEAM</c> scripting define for that build only (<see cref="BuildPlayerOptions.extraScriptingDefines"/>, so
    /// Player Settings are not changed); the Itch variants do not. Scenes are the enabled ones in File → Build Profiles
    /// (<see cref="EditorBuildSettings.scenes"/>). Output: <c>unity/DeadLetter/Builds/&lt;target&gt;-&lt;store&gt;/</c>.
    /// <code>
    /// Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildWindowsSteam -logFile -
    /// Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.Build -dlTarget linux -dlStore itch
    /// </code>
    /// Optional arguments: <c>-dlDevelopment</c> (development build), <c>-dlOut &lt;dir&gt;</c> (output folder; it is
    /// emptied first, so see <see cref="CheckOutputFolder"/> for what may be used),
    /// <c>-dlSteamAppId &lt;id&gt;</c> (writes <c>steam_appid.txt</c> next to the executable, for local testing only; never
    /// upload it). IL2CPP cannot cross-compile: build Windows on Windows, macOS on a Mac, Linux on Linux (or on Windows /
    /// Mac with the Linux IL2CPP toolchain package). Batch mode exits with code 1 on failure.
    /// <para>
    /// Steam builds first check that Steamworks.NET is installed and referenced by <c>DeadLetter.Runtime</c>
    /// (<see cref="CheckSteamworks"/>); without it the <c>DL_STEAM</c> code cannot compile.
    /// </para>
    /// <para>
    /// Switch is not here: it needs the NDA'd Switch build module from the Nintendo Developer Portal and is built by hand
    /// by a licensed developer (see unity/README.md).
    /// </para>
    /// </summary>
    public static class BuildScripts
    {
        public const string SteamDefine = "DL_STEAM";
        public const string ProductFileName = "DeadLetter";
        public const string SteamworksPackage = "com.rlabrecque.steamworks.net";
        /// <summary>Written into every output folder; a <c>-dlOut</c> folder outside <c>Builds/</c> is emptied only if it has one.</summary>
        public const string OutputMarker = ".dl-build-output";
        private const string ReadmeSteam = "unity/README.md, \"Steamworks.NET (director: one-time setup)\", steps 1-2";

        public enum Target { Windows, Mac, Linux }
        public enum Store { Steam, Itch }

        // ---- -executeMethod entry points ------------------------------------------------------------------------------
        public static void BuildWindowsSteam() => BuildOrExit(Target.Windows, Store.Steam);
        public static void BuildWindowsItch() => BuildOrExit(Target.Windows, Store.Itch);
        public static void BuildMacSteam() => BuildOrExit(Target.Mac, Store.Steam);
        public static void BuildMacItch() => BuildOrExit(Target.Mac, Store.Itch);
        public static void BuildLinuxSteam() => BuildOrExit(Target.Linux, Store.Steam);
        public static void BuildLinuxItch() => BuildOrExit(Target.Linux, Store.Itch);

        /// <summary><c>-dlTarget windows|mac|linux -dlStore steam|itch</c>.</summary>
        public static void Build()
        {
            string t = Arg("-dlTarget"), s = Arg("-dlStore");
            Target target;
            Store store;
            if (!TryParseTarget(t, out target) || !TryParseStore(s, out store))
            {
                Fail($"BuildScripts.Build: need -dlTarget windows|mac|linux and -dlStore steam|itch (got '{t}', '{s}').");
                return;
            }
            BuildOrExit(target, store);
        }

        [MenuItem("Dead Letter/Build/Windows (Steam)")] private static void MenuWindowsSteam() => BuildPlayer(Target.Windows, Store.Steam);
        [MenuItem("Dead Letter/Build/Windows (Itch)")] private static void MenuWindowsItch() => BuildPlayer(Target.Windows, Store.Itch);
        [MenuItem("Dead Letter/Build/macOS (Steam)")] private static void MenuMacSteam() => BuildPlayer(Target.Mac, Store.Steam);
        [MenuItem("Dead Letter/Build/macOS (Itch)")] private static void MenuMacItch() => BuildPlayer(Target.Mac, Store.Itch);
        [MenuItem("Dead Letter/Build/Linux (Steam)")] private static void MenuLinuxSteam() => BuildPlayer(Target.Linux, Store.Steam);
        [MenuItem("Dead Letter/Build/Linux (Itch)")] private static void MenuLinuxItch() => BuildPlayer(Target.Linux, Store.Itch);

        // ---- The build ------------------------------------------------------------------------------------------------
        /// <summary>Builds one player. Returns true on success.</summary>
        public static bool BuildPlayer(Target target, Store store)
        {
            string[] scenes = EditorBuildSettings.scenes.Where(sc => sc.enabled && !string.IsNullOrEmpty(sc.path)).Select(sc => sc.path).ToArray();
            if (scenes.Length == 0)
            {
                Debug.LogError("BuildScripts: no enabled scenes in the build profile / EditorBuildSettings.");
                return false;
            }

            if (store == Store.Steam && !CheckSteamworks(out string steamProblem))
            {
                Debug.LogError("BuildScripts: " + steamProblem);
                return false;
            }

            BuildTarget buildTarget = ToBuildTarget(target);
            string outDir = Arg("-dlOut");
            if (string.IsNullOrEmpty(outDir)) outDir = Path.Combine(ProjectRoot(), "Builds", FolderName(target, store));
            outDir = Path.GetFullPath(outDir);
            if (!CheckOutputFolder(outDir, out string outProblem))
            {
                Debug.LogError("BuildScripts: " + outProblem);
                return false;
            }
            if (Directory.Exists(outDir)) Directory.Delete(outDir, true);
            Directory.CreateDirectory(outDir);
            File.WriteAllText(Path.Combine(outDir, OutputMarker),
                "Dead Letter build output (BuildScripts). This folder is deleted and rebuilt by the next build into it.\n");

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                target = buildTarget,
                targetGroup = BuildTargetGroup.Standalone,
                locationPathName = Path.Combine(outDir, ExecutableName(target)),
                options = HasArg("-dlDevelopment") ? BuildOptions.Development : BuildOptions.None,
                extraScriptingDefines = store == Store.Steam ? new[] { SteamDefine } : new string[0],
            };

            // IL2CPP for this build; restored afterwards so ProjectSettings is not left modified.
            NamedBuildTarget named = NamedBuildTarget.Standalone;
            ScriptingImplementation previousBackend = PlayerSettings.GetScriptingBackend(named);
            object previousMacArch = null;
            try
            {
                PlayerSettings.SetScriptingBackend(named, ScriptingImplementation.IL2CPP);
                if (target == Target.Mac) previousMacArch = SetMacArchitecture("x64ARM64");   // universal

                Debug.Log($"BuildScripts: {target} / {store} → {options.locationPathName} ({scenes.Length} scenes, defines: {string.Join(",", options.extraScriptingDefines)})");
                BuildReport report = BuildPipeline.BuildPlayer(options);
                BuildSummary summary = report.summary;
                if (summary.result != BuildResult.Succeeded)
                {
                    Debug.LogError($"BuildScripts: {target} / {store} {summary.result}: {summary.totalErrors} error(s).");
                    return false;
                }

                MoveDoNotShipFolders(outDir, target, store);
                WriteSteamAppIdIfAsked(outDir, store);
                Debug.Log($"BuildScripts: {target} / {store} succeeded, {summary.totalSize / (1024 * 1024)} MB in {summary.totalTime}.");
                return true;
            }
            finally
            {
                PlayerSettings.SetScriptingBackend(named, previousBackend);
                if (previousMacArch != null) SetMacArchitecture(previousMacArch.ToString());
            }
        }

        private static void BuildOrExit(Target target, Store store)
        {
            bool ok;
            try { ok = BuildPlayer(target, store); }
            catch (Exception e)
            {
                Debug.LogException(e);
                ok = false;
            }
            if (!ok) Fail($"BuildScripts: {target} / {store} failed.");
        }

        private static void Fail(string message)
        {
            Debug.LogError(message);
            if (Application.isBatchMode) EditorApplication.Exit(1);
        }

        // ---- Pre-build checks -----------------------------------------------------------------------------------------
        /// <summary>
        /// Steam builds compile <c>DL_STEAM</c> code that uses Steamworks.NET: the package must be installed and
        /// <c>DeadLetter.Runtime.asmdef</c> must reference it by name. False with a message pointing to the README.
        /// </summary>
        public static bool CheckSteamworks(out string problem)
        {
            problem = null;
            if (UnityEditor.PackageManager.PackageInfo.FindForPackageName(SteamworksPackage) == null)
            {
                problem = $"Steam build needs the Steamworks.NET package ({SteamworksPackage}) in Packages/manifest.json. See {ReadmeSteam}.";
                return false;
            }
            string asmdef = Path.Combine(Application.dataPath, "DeadLetter", "Runtime", "DeadLetter.Runtime.asmdef");
            string[] refs = null;
            try
            {
                if (File.Exists(asmdef)) refs = JsonUtility.FromJson<AsmdefReferences>(File.ReadAllText(asmdef))?.references;
            }
            catch (Exception e)
            {
                problem = $"Could not read {asmdef}: {e.Message}. See {ReadmeSteam}.";
                return false;
            }
            if (refs == null || !refs.Contains(SteamworksPackage))
            {
                problem = $"Steam build needs \"{SteamworksPackage}\" in the references of Assets/DeadLetter/Runtime/DeadLetter.Runtime.asmdef (by name, not GUID). See {ReadmeSteam}.";
                return false;
            }
            return true;
        }

        /// <summary>The part of an .asmdef this reads (JsonUtility).</summary>
        [Serializable]
        public sealed class AsmdefReferences
        {
            public string[] references;
        }

        /// <summary>
        /// The output folder is deleted before each build, so refuse anything that could be more than a build: the
        /// Unity project or any folder containing it, a folder with an <c>Assets</c> folder or a <c>.git</c>, and the
        /// <c>Builds</c> folder itself. Folders inside the project's <c>Builds/</c> are fine; anywhere else must already
        /// hold <see cref="OutputMarker"/> (written by an earlier build into it) or not exist yet.
        /// </summary>
        public static bool CheckOutputFolder(string outDir, out string problem)
        {
            problem = null;
            StringComparison cmp = Application.platform == RuntimePlatform.LinuxEditor ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase;
            string dir = NormalizeDir(outDir);
            string root = NormalizeDir(ProjectRoot());
            string builds = NormalizeDir(Path.Combine(root, "Builds"));
            if (string.Equals(dir, root, cmp) || IsUnder(root, dir, cmp))
            {
                problem = $"-dlOut '{dir}' is the Unity project or a folder containing it; refusing to delete it.";
                return false;
            }
            if (string.Equals(dir, builds, cmp))
            {
                problem = $"-dlOut '{dir}' is the whole Builds folder (other builds and symbols live there); use a subfolder.";
                return false;
            }
            if (!Directory.Exists(dir)) return true;
            if (!Directory.EnumerateFileSystemEntries(dir).Any()) return true;   // empty: nothing to lose
            if (Directory.Exists(Path.Combine(dir, "Assets")) || Directory.Exists(Path.Combine(dir, ".git")) || File.Exists(Path.Combine(dir, ".git")))
            {
                problem = $"-dlOut '{dir}' contains an Assets folder or .git; refusing to delete it.";
                return false;
            }
            if (IsUnder(dir, builds, cmp)) return true;
            if (File.Exists(Path.Combine(dir, OutputMarker))) return true;
            problem = $"-dlOut '{dir}' is outside {builds} and has no {OutputMarker} from an earlier build; refusing to delete it. Use an empty or new folder.";
            return false;
        }

        private static string NormalizeDir(string path)
        {
            string full = Path.GetFullPath(path);
            string trimmed = full.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            return trimmed.Length == 0 || trimmed.EndsWith(":", StringComparison.Ordinal) ? full : trimmed;   // "/" and "C:\" stay
        }

        /// <summary><paramref name="child"/> is strictly inside <paramref name="parent"/> (both normalized).</summary>
        private static bool IsUnder(string child, string parent, StringComparison cmp)
        {
            string prefix = parent.EndsWith(Path.DirectorySeparatorChar.ToString(), StringComparison.Ordinal) ? parent : parent + Path.DirectorySeparatorChar;
            return child.Length > prefix.Length && child.StartsWith(prefix, cmp);
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        public static string FolderName(Target target, Store store) => target.ToString().ToLowerInvariant() + "-" + store.ToString().ToLowerInvariant();

        private static BuildTarget ToBuildTarget(Target t)
        {
            switch (t)
            {
                case Target.Windows: return BuildTarget.StandaloneWindows64;
                case Target.Mac: return BuildTarget.StandaloneOSX;
                default: return BuildTarget.StandaloneLinux64;
            }
        }

        private static string ExecutableName(Target t)
        {
            switch (t)
            {
                case Target.Windows: return ProductFileName + ".exe";
                case Target.Mac: return ProductFileName + ".app";
                default: return ProductFileName + ".x86_64";
            }
        }

        private static string ProjectRoot() => Path.GetFullPath(Path.Combine(Application.dataPath, ".."));

        /// <summary>
        /// IL2CPP writes <c>*_BackUpThisFolder_ButDontShipItWithYourGame</c> (symbols) and Burst may write
        /// <c>*_BurstDebugInformation_DoNotShip</c> beside the player. Move them to <c>Builds/symbols/&lt;target-store&gt;/</c>
        /// so <c>butler push</c> and the Steam depot can upload the output folder as it is. Keep the symbols for crash dumps.
        /// </summary>
        private static void MoveDoNotShipFolders(string outDir, Target target, Store store)
        {
            string symbols = Path.Combine(ProjectRoot(), "Builds", "symbols", FolderName(target, store));
            foreach (string dir in Directory.GetDirectories(outDir))
            {
                string name = Path.GetFileName(dir);
                if (!name.EndsWith("_ButDontShipItWithYourGame", StringComparison.Ordinal) &&
                    !name.EndsWith("_DoNotShip", StringComparison.Ordinal)) continue;
                Directory.CreateDirectory(symbols);
                string dest = Path.Combine(symbols, name);
                if (Directory.Exists(dest)) Directory.Delete(dest, true);
                Directory.Move(dir, dest);
            }
        }

        /// <summary>Local testing of a Steam build outside Steam: <c>-dlSteamAppId 480</c> writes steam_appid.txt.</summary>
        private static void WriteSteamAppIdIfAsked(string outDir, Store store)
        {
            string id = Arg("-dlSteamAppId");
            if (store != Store.Steam || string.IsNullOrEmpty(id)) return;
            // Next to the .exe / .x86_64 / .app (Steam reads it from the working directory when launched by hand).
            File.WriteAllText(Path.Combine(outDir, "steam_appid.txt"), id.Trim());
            Debug.LogWarning("BuildScripts: wrote steam_appid.txt for local testing. Do not upload this build to Steam.");
        }

        /// <summary>
        /// macOS architecture lives in <c>UnityEditor.OSXStandalone.UserBuildSettings.architecture</c>, which only exists
        /// when the Mac build module is installed; it is set by reflection so this file compiles without the module.
        /// Returns the previous value (to restore), or null if it could not be set.
        /// </summary>
        private static object SetMacArchitecture(string value)
        {
            Type type = AppDomain.CurrentDomain.GetAssemblies()
                .Select(a => a.GetType("UnityEditor.OSXStandalone.UserBuildSettings", false))
                .FirstOrDefault(t => t != null);
            PropertyInfo prop = type?.GetProperty("architecture", BindingFlags.Public | BindingFlags.Static);
            if (prop == null || !prop.PropertyType.IsEnum)
            {
                Debug.LogWarning("BuildScripts: macOS UserBuildSettings.architecture not found; set Architecture = Intel 64 + Apple silicon in the build profile by hand.");
                return null;
            }
            object previous = prop.GetValue(null);
            try { prop.SetValue(null, Enum.Parse(prop.PropertyType, value)); }
            catch (Exception e)
            {
                Debug.LogWarning($"BuildScripts: could not set macOS architecture to {value}: {e.Message}");
                return null;
            }
            return previous;
        }

        private static bool TryParseTarget(string s, out Target t)
        {
            switch ((s ?? "").ToLowerInvariant())
            {
                case "windows": case "win": case "win64": t = Target.Windows; return true;
                case "mac": case "macos": case "osx": t = Target.Mac; return true;
                case "linux": case "linux64": t = Target.Linux; return true;
                default: t = Target.Windows; return false;
            }
        }

        private static bool TryParseStore(string s, out Store st)
        {
            switch ((s ?? "").ToLowerInvariant())
            {
                case "steam": st = Store.Steam; return true;
                case "itch": case "drmfree": st = Store.Itch; return true;
                default: st = Store.Itch; return false;
            }
        }

        private static string[] _args;
        private static string[] Args => _args ?? (_args = Environment.GetCommandLineArgs());

        private static bool HasArg(string name) => Args.Any(a => string.Equals(a, name, StringComparison.OrdinalIgnoreCase));

        private static string Arg(string name)
        {
            string[] a = Args;
            for (int i = 0; i < a.Length - 1; i++)
                if (string.Equals(a[i], name, StringComparison.OrdinalIgnoreCase)) return a[i + 1];
            return null;
        }

        /// <summary>For tooling: every desktop method name, as passed to -executeMethod.</summary>
        public static IEnumerable<string> ExecuteMethods()
        {
            foreach (Target t in Enum.GetValues(typeof(Target)))
                foreach (Store s in Enum.GetValues(typeof(Store)))
                    yield return "DeadLetter.Editor.Build.BuildScripts.Build" + t + s;
        }
    }
}
