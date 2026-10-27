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
   Input System 1.14 may apply default stick deadzone processing to `<Gamepad>/leftStick/x` before the motor's
   own 0.22 deadzone and 0.65 run threshold — check the action's processors and remove the default deadzone if it
   double-applies.
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

## D17 motor (U-11)

D-17's movement, interaction and act timing are Core code, ported from `game/undelivered/index.html`
(`updatePlayer` L1931–2067 and the act/hold code cited in `docs/unity/port_architecture.md` §4.7–4.12).

```
Assets/DeadLetter/Core/
  Maths/        Vec2, Smooth (smoothstep, frame-rate-exact decay)
  Motor/        MotorConfig    every constant, with the index.html line it comes from
                D17Motor       fixed-step state machine: walk/run/crouch, jump (coyote + buffer), mantle, mid-air
                               catch, carry, push/pull, acts (lift, set down, place, grab, present, sit, use)
                ClipTimings    d17.glb clip lengths + LOOP_FRAMES + the clip-frame events acts fire on
                IMotorWorld    ground / ceiling / wall / ledge probes in the lane; BoxWorld = box implementation
                MotorInput     one step's input (Move, Jump, Use, Run modifier, Crouch)
  Interaction/  Contracts      ICarryable, IPlaceTarget, IPushable, IPresentTarget, ISeat, IUsable (U-10 implements)
                InteractionResolver, PlaceSearch
Assets/DeadLetter/Runtime/
  Player/       D17Controller  MonoBehaviour: input → FixedTick (Update) → D17Motor; physics probes; transform + Animator
                D17AnimatorParams  Animator parameter names (states are named after the clips)
  Input/        DeadLetter.inputactions  Gameplay map: Move, Jump, Crouch, Use, Run, Pause, Checkpoint
```

Run the tests with `dotnet test unity/core-tests` (`D17MotorTests`, `InteractionTests`, `ClipTimingsTests`).
They check the prototype's numbers: jump apex and velocity, speeds, coyote and buffer windows, the mantle band
(0.24 < h ≤ 0.62 standing, ≤ 0.72 caught mid-air), step-up, crouching under ceilings, the 56-frame climb, act
event frames, the resolver's in-front rule, and that the same inputs give the same trace.

**To use it in a scene:** add `D17Controller` to D-17's root, assign `DeadLetter.inputactions` and the Animator.
Put D-17's own colliders on a layer outside the probe masks. Set `groundMask` (floors, crates, walls),
`ceilingMask` (undersides) and `rampMask`. Every Animator state needs its Speed Multiplier bound to `ClipSpeed`.
Core runs at 60 Hz from `Update` (`Time.deltaTime` through `FixedTick`), whatever `Time.fixedDeltaTime` is, and the
transform is interpolated with `FixedTick.Alpha`. The lane probes are raycasts against static colliders; if moving
colliders are added to the probe masks, sync transforms (`Physics.SyncTransforms`) before the Core tick.

**D-17 asset and Animator (U-11 slice 2).** `Assets/Art/D17/d17.glb` is the shipped `game/undelivered/assets/d17.glb`
copied unchanged (skinned rig, 26 joints, 76 clips). glTFast imports it; `Editor/Import/D17ImportSettings` pins the
import to **Animation = Mecanim** (generic clips, an `Animator` on the imported root) and original-unique node names.
`D17AssetTests` (core-tests) checks every `ClipTimings` clip is in that GLB with the same frame count.

First open, after the import finishes:

1. Run **Dead Letter → Build → D17 Animator**. It writes `Assets/Art/D17/D17.controller`: one state per clip, named as
   the clip, Speed Multiplier bound to `ClipSpeed`; each one-shot clip also gets a `Name (hold)` state that freezes its
   last frame (glTFast marks every clip as looping). Re-run it after any re-export of `d17.glb`; it rebuilds in place
   and keeps the GUID. Check the Console for clip/length warnings.
2. Drag `d17.glb` into the scene (or a prefab). Assign `D17.controller` to the `Animator` glTFast put on the root
   (the clips' curve paths are relative to that object; do not move the Animator to a child). Add `D17Controller`
   to the same root or a parent and assign that Animator.
3. Commit `D17.controller` and the `.meta` files.

## Cameras and directed moments (U-13)

The lane camera, its framing volumes, the four prologue moments and the cue clock are Core code, ported from
`game/undelivered/index.html`. The sources are `frameFor`/`updateCamera` (L7644–7806), `applyShots`/`currentShot` (L3687–3836),
`MOMENTS` (L945–964) and `Music.momentTime` (L905–927). See `docs/unity/port_architecture.md` §4.17, §4.18 and §4.24,
and `docs/directed_moments.md`.

```
Assets/DeadLetter/Core/
  Maths/    Vec3 (prototype axes, ToUnity = (x, y, −z)), Damp (exact-at-60 Hz exponential easing)
  Camera/   CameraConfig    every rig constant, with its index.html line; lens maths (widthFit, filmGauge 36 → vertical FOV)
            Framing         FramingZone / FramingTrack: framing volumes as data (x/y blends, signal gates, nested zones,
                            fit width, cx clamp, lead, fog), evaluated exactly as frameFor
            PrologueFraming DL-01 to DL-07 (floor and gallery) transcribed as zones + the signals scene rules publish
            CameraRig       follow lag, push-in, height follow, ending fog, shot blend 1.4 in / 0.8 out, shake, opening
            MomentShots     the camera beats of kin / refuge / ringc / window on their cue clocks; ring C's cold light
  Cues/     IMusicClock     the audio clock interface (Runtime: AudioDspMusicClock; tests: a fake)
            CueClock        momentTime: heard time from the scheduled start minus output latency; monotonic; freezes
                            when paused; falls back to the sim clock (no music, 0.6 s unstarted, 2.0 s stalled)
            DirectedMoment  lock / release / control (L948) + peak; PrologueMoments.Kin/Refuge/RingC/Window
            MomentDirector  startMoment / momentShot / momentFree / voicesHeld + GateInput(MotorInput) for D-17
Assets/DeadLetter/Runtime/Camera/
            LaneCameraDriver      steps CameraRig on every Core step (D17Controller.Stepped), interpolates, writes a
                                  CinemachineCamera (or a Camera) and the fog
            AudioDspMusicClock    IMusicClock on AudioSettings.dspTime: buffer smoothing, pause, per-platform latency
            DirectedMomentPlayer  Trigger(name): cue via PlayScheduled 0.1 s ahead, input gate, Timeline scrubbed to the
                                  cue clock, moment shot handed to the camera
```

**Moment timing (seconds from the trigger, the cue's first sample as heard).**

| Moment | lock | release (shot lets go, voices back) | control back | peak |
|---|---|---|---|---|
| `kin` (DL-04) | 19 | 21 | 22.5 | 15 |
| `refuge` (DL-09) | 14 | 16 | **16.6** + his turn home (the awe act stops waiting at release + 0.6, L3390; `MOMENTS` says 18.5) | 10 |
| `ringc` (DL-10) | 16 | 20 | 22 | 12 |
| `window` (end) | never | 13.6 (label check) | never: the ending sequence owns him | 6.5 |

Before `lock`, input is withheld. From `lock`, any input (move, use or jump) cuts the hold, and control comes back on that step.
`MomentDirector.GateInput` returns `MotorInput.None` while the moment holds him, including on the step where control comes
back. Raw input passes from the next step. Each moment's act condition (kin's realise act idle, refuge's awe clip done,
ringc's car gone) is passed in as `actReady` (`DirectedMomentPlayer.ActReady`).

**Deviations from the prototype.**
- Every `x += (t − x)·min(1, dt·k)` easing is `Damp`. It is exact at 60 Hz and frame-rate independent, so the 30 fps
  Switch build frames the same as PC. The prototype lags differently at each frame rate.
- The rig steps on the fixed 60 Hz Core step and is render-interpolated. The prototype stepped once per rendered frame.
- A moment shot still uses the cue-clock delta (clamped to 0.5 s) as its dt, as in the prototype.
- `MusicFailed` and the stalled fallbacks follow L918–919. Unity has no `getOutputTimestamp`, so the DSP clock is
  extrapolated by up to one mix buffer instead.
- The camera maths is in the prototype's axes, and only `LaneCameraDriver` converts to Unity's.
- Not yet transcribed as framing data, because they arrive with their scene ports: DL-07's `watchLoad` wide frame (its
  centre and width move with x), DL-08–DL-11 (`k4`, `k5`), chapter 1 (`frameAtt`, `frameAtt2`; restore DL-17's volume,
  §9 #1), and the non-moment authored shots (label, scan, pit, knock…, a `ShotSelector`).

**Scene setup.** Add these to `DL_Persistent`:
1. One `CinemachineBrain` on the main Camera.
2. One `CinemachineCamera` "Lane" with **no Position/Rotation Control and no noise**. Cinemachine must leave its
   transform alone.
3. `LaneCameraDriver`, with `player` set to `D17Controller` and the Lane camera assigned.
4. `AudioDspMusicClock`. Fill in the per-platform latency offsets once measured. Switch is still to be measured.
5. `DirectedMomentPlayer`, with one binding per moment: the cue `AudioSource` (`playOnAwake` off) and an optional
   `PlayableDirector` (Timeline `Moment_kin` …).

Scene rules call `DirectedMomentPlayer.Trigger("kin")` at the prototype's triggers. They publish framing signals in
`LaneCameraDriver.Signals` (`dl02`, `dl02.reveal`, `dl02.realised`, `dl06.pit`; see `PrologueFraming`). They also set the
driver's transit, slow-pace and well flags.

Tests: `CameraRigTests` checks the zones against a literal transcription of `frameFor` along x 0–80, including portrait
and gallery heights. It also checks the blends, damping convergence and frame-rate independence, the shot blend, the
cue-clock dt and determinism. `CueClockTests` checks lock, release and control per moment, the cut, latency, pause,
the fallbacks, the ring C light and determinism.

**Unverified (no editor here).** The Runtime files compile only against stubs.
- Cinemachine 3's `CinemachineCamera.Lens` / `LensSettings.FieldOfView` field.
- Whether a CinemachineCamera with no behaviours really keeps its transform.
- `DefaultExecutionOrder(-100)` running before the Brain.
- Whether `PlayableDirector` in `Manual` mode needs `Play()` before `Evaluate()`.
- Whether `AudioSettings.dspTime` keeps running while `AudioListener.pause` is set.
- Whether `GetDSPBufferSize` × buffers overstates latency on some platforms.

## Platforms and settings (U-17)

Store layer, player options, accessibility and command-line builds for Steam, Itch (DRM-free) and Switch (stub).
See `docs/unity/port_architecture.md` §4.4, §4.29 and §4.30.

```
Assets/DeadLetter/Core/
  Settings/   GameSettings        every option + default; the prototype's options card (OPTS L8283, brightness L8307–8319)
                                  ported key for key, then the port's additions
              SettingsSerializer  key=value text, hand-written key table (no reflection, IL2CPP-safe), unknown keys kept,
                                  bad values → default, out-of-range → clamped, never throws, stable output
              AudioLevels         slider → dB for the five mixer groups; Sound/Music toggles
  Platform/   IPlatformServices   achievements, rich presence, overlay-opened event, CloudSync; NullPlatformServices
              ICloudSync          whole-file cloud blobs (U-14's ISaveStore can wrap it later)
              Achievements        the catalog: empty for now (how to add one is in the file)
              GlyphRules          which button-prompt set to draw (keyboard / Xbox / PlayStation / Switch / Steam Deck)
              PauseGate           player pause + overlay + focus loss; a system interruption leaves the pause card up
Assets/DeadLetter/Runtime/
  Platform/   PlatformServices    compile-time factory + Current; PlatformServicesHost (DL_Persistent): init, tick, pause
              SteamPlatformServices (#if DL_STEAM), ItchPlatformServices (no-op), SwitchPlatformServices (NDA stub)
              GlyphTracker        last device used → GlyphRules
  Settings/   SettingsStore       persistentDataPath/settings.cfg; applies mixer, calm, brightness/bloom, bindings
              BindingRebinder     PerformInteractiveRebinding + SaveBindingOverridesAsJson / LoadBindingOverridesFromJson
Assets/DeadLetter/Editor/Build/BuildScripts   -executeMethod player builds (IL2CPP; Steam/Itch variants)
tools/build/itch_push.sh                      butler push helper (documented, not run)
tools/build/steam/app_build.vdf               ContentBuilder template (placeholders only)
```

Tests: `SettingsTests` (defaults against `OPTS`, round trip, stable output, unknown-key preservation, corrupt and
truncated input, clamping, culture invariance, dB maths) and `PlatformTests` (glyph selection, pause gate, no-op
services, achievement ids). Run `dotnet test unity/core-tests`.

### Options

| Option | Default | Source |
|---|---|---|
| Auto-run (hold Shift or B to walk) | on | `autorun: true`, L170, L8283 → `D17Motor.AutoRun` |
| Sound | on | L171; off mutes SFX, Voice, Ambience |
| Music | on | L172; off mutes Music |
| Light up things I can use, and show the button | on | `prompts`, L173 |
| Show a button prompt if I'm stuck | off | `assist`, L174 |
| Reduce flicker and flashes (calm) | off | `calm`, L176: no flicker, flashes, shake or sparks; bloom 0.35 instead of 0.55 |
| Brightness | 1.0 (0.8–1.8) | L175, L8308; URP post-exposure log2(v) on top of the authored look |
| Share anonymous play data | **off** | prototype default is on; §4.30 says the shipped uploader is opt-in. **Director to confirm.** |
| Master / Music / SFX / Voice / Ambience volume | 1.0 each | new; linear sliders → `AudioMixer.SetFloat(name, 20·log10 v)` (−80 dB floor) |
| Text size (subtitles, letters) | Default (×1.0; Small 0.85, Large 1.25, Extra large 1.6) | new |
| Text background panel | off | new (§4.29) |
| Colour-independent cues | off | new; every colour-only cue also gets a shape or pattern when on |
| Hold actions toggle | off | new (§4.29: DL-16's held lever) |
| Button prompts | Auto | new; Auto follows the last device used |
| Key bindings | defaults | new; Input System override JSON |

Settings are per device and are not cloud-synced (a Deck and a desktop want different text and glyphs).

**Hooks wired:** `D17Controller` takes auto-run from `SettingsStore.Applied` (its serialized `autoRun` is used only
when no store exists). `LaneCameraDriver.Shake` honours `SettingsStore.Calm`. **Hooks still needed** as their systems
land: every light flicker, spark and flash source must read `SettingsStore.Calm` (§4.14, §4.20, §4.22); the glint/
prompt view reads `Prompts` and `StuckAssist`; the subtitle/letter UI reads `TextScale` and `TextBackground`; colour
cues read `ColourIndependentCues`; DL-16's lever reads `ToggleHolds`; the telemetry uploader (§4.30) reads `Telemetry`.
The options and pause screens (UI Toolkit) are not built yet: they edit `SettingsStore.Current.Clone()` and call
`SettingsStore.Instance.Commit(draft)` on Confirm, or `RevertBindings()` on Cancel.

**Scene setup** (`DL_Persistent`): add `SettingsStore` (assign the U-16 mixer, `DeadLetter.inputactions` and the global
post Volume) and `PlatformServicesHost` (assign D-17 and the `DirectedMomentPlayer`). The U-16 mixer must expose its
group volumes as exactly `Master`, `Music`, `SFX`, `Voice`, `Ambience`.

### Scripting defines

| Define | Set by | Effect |
|---|---|---|
| `DL_STEAM` | `BuildScripts` Steam methods (per build, via `BuildPlayerOptions.extraScriptingDefines`; Player Settings are not changed). For the editor, add it by hand in Player Settings → Scripting Define Symbols. | compiles `SteamPlatformServices` (standalone targets only) |
| `UNITY_SWITCH` | Unity, when the Switch module is the build target | chooses `SwitchPlatformServices` |
| neither | Itch builds, editor default | `ItchPlatformServices` (no-ops) |

If Steam fails to start, the game logs a warning and carries on with the no-op services.

### Building

IL2CPP does not cross-compile: build Windows on Windows, macOS on a Mac, Linux on Linux (or with Unity's Linux
IL2CPP toolchain package). Each OS needs its Unity build-support module with IL2CPP. Scenes come from the enabled
entries in the build profile (EditorBuildSettings). Output goes to `unity/DeadLetter/Builds/<target>-<store>/` (ignored),
and IL2CPP/Burst do-not-ship folders are moved to `Builds/symbols/<target>-<store>/` (keep them for crash symbols).

```
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildWindowsSteam -logFile -
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildWindowsItch  -logFile -
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildMacSteam     -logFile -
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildMacItch      -logFile -
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildLinuxSteam   -logFile -
Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildLinuxItch    -logFile -
# or: -executeMethod DeadLetter.Editor.Build.BuildScripts.Build -dlTarget windows|mac|linux -dlStore steam|itch
# options: -dlDevelopment, -dlOut <dir>, -dlSteamAppId <id> (local Steam testing only: writes steam_appid.txt; never upload)
```

The same builds are under **Dead Letter → Build** in the editor menu. macOS is built universal (Intel + Apple silicon)
through `UserBuildSettings.architecture`, set by reflection; if the Console says it was not found, set it in the build
profile by hand. Code signing and notarisation for macOS are not automated.

Uploads: `tools/build/itch_push.sh <version>` (butler; see its header) and `tools/build/steam/app_build.vdf` (fill the
placeholders, then `steamcmd +login <account> +run_app_build <path> +quit` from the Steamworks SDK's ContentBuilder).

**Switch is human-only.** The Switch build module and the NintendoSDK are under NDA and come from the Nintendo
Developer Portal. A licensed developer installs them on a licensed machine, builds from the editor's Switch build profile,
and implements the TODOs in `SwitchPlatformServices` (user selection, save-data mount/commit, focus/HOME handling).
None of that can be done or checked from this repo's cloud sessions, and no Switch SDK names appear in the code.

### Steamworks.NET (director: one-time setup)

1. Add this line to `Packages/manifest.json` → `dependencies` (pick the latest release tag from
   https://github.com/rlabrecque/Steamworks.NET/releases and put it after `#`):
   ```
   "com.rlabrecque.steamworks.net": "https://github.com/rlabrecque/Steamworks.NET.git?path=/com.rlabrecque.steamworks.net#<tag>",
   ```
2. Add `"com.rlabrecque.steamworks.net"` to the `references` of `Assets/DeadLetter/Runtime/DeadLetter.Runtime.asmdef`
   (after `"DeadLetter.Core"`). It is safe without `DL_STEAM`: nothing outside `#if DL_STEAM && UNITY_STANDALONE` uses it.
   (Optional, to keep the Itch build free of `steam_api` libraries: install the package only on the Steam build
   machine, or exclude the plugin's platforms in its importer. Shipping the unused native library in the Itch build is
   harmless but untidy.)
3. Set `SteamPlatformServices.AppId` to the real App ID when it exists (0 = skip the restart-through-Steam check).
4. **steam_appid.txt:** for the editor, put a file `unity/DeadLetter/steam_appid.txt` containing just the App ID (480,
   Valve's Spacewar test app, works before the real one exists). It is git-ignored. For a local player build outside Steam use
   `-dlSteamAppId <id>`. Never ship the file: Steam supplies the ID when it launches the game, and the depot script excludes it.
5. Create achievements on the partner site with the same API names as `Core/Platform/Achievements.cs` (empty for now).
   Rich presence needs a localisation file with `steam_display` tokens uploaded on the partner site.

### Steam Deck checklist

- [ ] Default text is legible at 1280×800 on a 7" screen: check subtitles, letters and prompts at Text size Default.
      Valve's Deck Verified review fails very small text; Large / Extra large must not clip or overflow.
- [ ] Glyphs: Auto shows Steam Deck prompts on a Deck (`SteamUtils.IsSteamRunningOnSteamDeck()`, or `SteamDeck=1`
      in the environment for non-Steam builds) and Keyboard once a keyboard is used. Steam Deck glyph art is needed.
- [ ] Every action works on the Deck's controls with the default Steam Input (gamepad) configuration; no mouse-only UI.
- [ ] Rebinding works with a pad (Escape cancels on keyboard; add a pad cancel button in the options UI).
- [ ] The Steam overlay (Steam button) pauses the game and leaves the pause card up when it closes.
- [ ] Suspend / resume (power button) pauses the game (focus loss → `PauseGate`) and audio resumes cleanly.
- [ ] 16:10 aspect: framing and UI at 1280×800 (the camera's width fit should hold; check letterboxing).
- [ ] Default graphics hold a stable 30 or 60 fps on the Deck (choose the Switch-like quality tier if not).
- [ ] The text input for any name field uses the Steam on-screen keyboard (none exist yet).
- [ ] Linux depot runs natively on SteamOS, or the Windows depot runs under Proton (test both; mark the one you ship).

### Unverified (no editor here)

The Runtime and Editor files were type-checked against hand-written stubs only.
- Steamworks.NET: `SteamUtils.IsSteamRunningOnSteamDeck()` is present in the chosen tag; `Callback<T>.Dispose()`;
  achievements without `RequestCurrentStats()` (fine on Steamworks SDK 1.61+, older SDKs need it after Init).
- `UnityEditor.OSXStandalone.UserBuildSettings.architecture` and its `x64ARM64` value in Unity 6 (set by reflection).
- `PlayerSettings.Get/SetScriptingBackend(NamedBuildTarget, …)` restore after a build in batch mode leaving no diff.
- `AudioMixer.SetFloat` ignored in Awake (the store applies in Start); check the levels on the first frame.
- The bloom scale (calm 0.35 / normal 0.55 of the authored URP intensity) is a proportional guess, not a match to
  three.js's UnrealBloom strength.
