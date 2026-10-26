# Dead Letter — Unity project

Unity 6 LTS + URP project skeleton (issue #3, task U-02). The Unity project lives in
`unity/DeadLetter/`; an engine-free .NET test harness lives in `unity/core-tests/`.

## Unity version

`ProjectSettings/ProjectVersion.txt` says `6000.3.0f1`. That patch number is a placeholder
chosen without access to Unity's servers. **Install the newest 6000.3 LTS in Unity Hub and
open the project with it; Unity will offer to upgrade the version file.** Accept, and commit
the updated `ProjectVersion.txt`.

## Opening the project

Unity Hub → Add → Add project from disk → select `unity/DeadLetter/` → open with 6000.3 LTS.
The first import takes a while (it builds `Library/`, which is ignored).

## First-open checklist (do these once, then commit)

1. **Commit the generated `.meta` files.** None were written by hand. Unity generates one for
   every file and folder under `Assets/` and `Packages/` on first import. Commit all of them
   in one go, along with any `ProjectSettings/*.asset` and `Packages/packages-lock.json`
   Unity creates. Until that commit lands, everyone else's GUIDs will be different.
2. **Package versions.** If the Package Manager reports a version it can't resolve, pick the
   version it offers in Window → Package Manager. See the table below.
3. **Input System prompt.** When Unity asks whether to enable the new input backends,
   choose **Yes** (the editor restarts). Then check Project Settings → Player → Other
   Settings → *Active Input Handling* = **Input System Package (New)**.
4. **Player settings** (Project Settings → Player). These were left out on purpose: a
   hand-written `ProjectSettings.asset` with the wrong serialized schema is worse than none.
   - Company Name: `DeadLetter` (no company name is defined in `docs/`)
   - Product Name: `Dead Letter`
   - Other Settings → Rendering → Color Space: **Linear**
   - Other Settings → Configuration → Scripting Backend (Standalone/PC tab): **IL2CPP**
5. **URP pipeline asset.** Assets → Create → Rendering → URP Asset (with Universal Renderer)
   and save it into `Assets/Settings/`. Assign it in Project Settings → Graphics → Default
   Render Pipeline and in Project Settings → Quality (each quality level).
6. **Smart Merge** (each machine, once). This is needed for the `merge=unityyamlmerge` lines in `/.gitattributes`:
   ```
   git config merge.unityyamlmerge.name "Unity SmartMerge"
   git config merge.unityyamlmerge.driver '"<UnityEditor>/Data/Tools/UnityYAMLMerge" merge -p %O %B %A %A'
   git config merge.unityyamlmerge.recursive binary
   ```
   Also set Project Settings → Editor → Asset Serialization = **Force Text** and Version
   Control = **Visible Meta Files**. Both are the Unity 6 defaults, but check them.
7. Run Window → General → Test Runner → EditMode → Run All. `FixedTickTests` should pass.

## Packages (`Packages/manifest.json`)

These were chosen offline, because the Unity package registry is unreachable from the build
container. Where unsure, the version that ships with Unity 6000.0 LTS was used. Unity can
upgrade a package forward when it opens the project, but it cannot resolve a version that
doesn't exist.

| Package | Version | Confidence |
|---|---|---|
| com.unity.render-pipelines.universal | 17.0.3 | High that it exists. It's the 6000.0 line. URP is an editor-locked core package, so 6000.3 should move it to its bundled 17.3.x on open. |
| com.unity.inputsystem | 1.14.0 | Medium-high |
| com.unity.cinemachine | 3.1.2 | High |
| com.unity.timeline | 1.8.7 | High |
| com.unity.cloud.gltfast | 6.8.0 | Medium. Newer 6.x releases probably exist. |
| com.unity.test-framework | 1.4.5 | Medium-high. Core package, may be moved forward on open. |
| com.unity.ugui | 2.0.0 | High |
| com.unity.ide.visualstudio | 2.0.22 | High. Add `com.unity.ide.rider` yourself if you use Rider. |
| com.unity.modules.* | 1.0.0 | High. This is the standard Unity 6 template set. |

## Code layout and assemblies

```
Assets/DeadLetter/
  Core/      DeadLetter.Core      noEngineReferences: pure C#, no UnityEngine
  Runtime/   DeadLetter.Runtime   MonoBehaviours, URP, Input System, Cinemachine, Timeline; refs Core
  Editor/    DeadLetter.Editor    editor-only tooling; refs Core + Runtime
  Tests/EditMode  DeadLetter.Tests.EditMode  (Editor platform, UNITY_INCLUDE_TESTS, nunit)
  Tests/PlayMode  DeadLetter.Tests.PlayMode  (UNITY_INCLUDE_TESTS, nunit)
Assets/Art, Assets/Audio, Assets/Scenes, Assets/Settings
```

**Why the split matters:** `Core` cannot reference the engine. It holds the simulation and
rules: deterministic ticks, puzzle state, save data, and the letter/route logic. Cloud and CI
sessions have no Unity editor, so they can compile and unit-test `Core` with the plain .NET
SDK. `Runtime` is the thin layer that connects `Core` to Unity: scenes, input, cameras,
rendering. `Editor` is never shipped. Keep logic in `Core` wherever you can, and keep
`UnityEngine` types (`Vector3`, `Mathf`, `Time`) out of it. The `noEngineReferences` flag
enforces that.

## Running Core tests without Unity

`unity/core-tests/` is an SDK-style xUnit project. It compiles
`DeadLetter/Assets/DeadLetter/Core/**/*.cs` directly, with `LangVersion 9.0` to match Unity's
C# compiler.

```
dotnet test unity/core-tests
```

It needs the .NET 8 SDK or newer. In the cloud container, `dot.net` / `builds.dotnet.microsoft.com`
are blocked by the proxy. The SDK was installed by extracting Ubuntu's `dotnet-sdk-8.0` debs
(`apt-get download` + `dpkg -x`) into a scratch directory, outside the repo. NuGet
restore from api.nuget.org works.

## Git LFS status

`git-lfs 3.4.1` is installed in the container, and the LFS filters are configured globally.
`git lfs env` reports the endpoint `https://github.com/nsmith-gd/deadletter.git/info/lfs`
with `auth=none`. Nothing was pushed, so it has **not** been confirmed that an LFS upload
gets through the proxy. The LFS patterns in `/.gitattributes` are **commented out**. The repo
already stores ~200 binaries (png/mp3/mp4/glb/blend) as normal git objects, so turning LFS
on is a director decision. The options are a migrate (history rewrite) or LFS for new files
only. After deciding, uncomment the patterns and make a test push from a desktop machine.
