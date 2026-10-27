using DeadLetter.Runtime.Platform;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

namespace DeadLetter.Editor.Build
{
    /// <summary>
    /// Fails every Switch build while <see cref="SwitchPlatformServices"/> is still the stub
    /// (<see cref="SwitchPlatformServices.IsStub"/>), so a build whose save data, user selection and focus handling do
    /// nothing cannot ship by accident. Runs for editor and command-line builds alike. <c>BuildTarget.Switch</c> is in
    /// the enum without the Switch module installed, so this compiles everywhere.
    /// </summary>
    public sealed class SwitchStubBuildGuard : IPreprocessBuildWithReport
    {
        public int callbackOrder => -1000;

        public void OnPreprocessBuild(BuildReport report)
        {
            if (report.summary.platform == BuildTarget.Switch && SwitchPlatformServices.IsStub)
                throw new BuildFailedException(
                    "Dead Letter: SwitchPlatformServices is still a stub (IsStub = true): no user selection, save-data " +
                    "mount/commit or focus handling. Implement its TODOs and set IsStub = false first; see unity/README.md, " +
                    "\"Platforms and settings (U-17)\" → \"Switch is human-only\".");
        }
    }
}
