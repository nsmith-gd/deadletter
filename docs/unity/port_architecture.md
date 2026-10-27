# Dead Letter: Unity port architecture (U-01)

**Issue:** nsmith-gd/deadletter#2 (task U-01). **Status:** draft for the director, 26 October 2026.
**Source read:** `game/undelivered/index.html` at commit `7b3c123` (8,633 lines, three.js 0.169.0), all of it, plus
`game/undelivered/README.md`, `docs/full_game_plan.md` §5, `docs/directed_moments.md`, `docs/direction.md`
(*Performance budget*, *Lights: a fixed pool*), `docs/scenes/DL-01_the_wake.md` §8, `docs/chapter1_build_spec.md` §1,
`tools/sim/`. Asset counts were measured from `game/undelivered/assets/*.json|glb` with a glTF parser (§8).

**Who reads what.** Each downstream task can start from its sections here plus the cited line ranges:

| Task | Read |
|---|---|
| U-10 mechanism framework (Core) | §2, §3, §4.6, §4.9–4.16, §5, §6 |
| U-11 D-17 motor, interaction, carry, animator | §3, §4.4–4.12, §4.19 |
| U-12 Blender → Unity art pipeline | §0.2, §4.1, §4.3, §6, §8, §9 |
| U-13 cameras, directed moments, cue clock | §4.17, §4.18, §4.24 |
| U-14 checkpoints and save | §4.28, §5 (checkpoint column) |
| U-15 look: lights, pool, fog, post, tiers | §4.2, §4.3, §4.20–4.22, §8 |
| U-16 audio | §4.23–4.25 |
| U-17 platform, settings, accessibility | §4.4, §4.29, §4.30 |
| U-18 headless replay harness (port of `tools/sim`) | §3.1, §4.31 |
| U-20/21/22 scene ports | §5 (one row per scene) and the system sections it names |

---

## 0. Conventions used in this document

### 0.1 References

- `L1931–2067` = lines of `game/undelivered/index.html` at `7b3c123`. Constants are quoted with the line that defines
  them. A value like `OFF3 + 52.45` is also given resolved (here 85.45) because the offsets are part of the lane.
- **Offsets (L274):** `OFF2 = 13`, `OFF3 = 33`, `OFF4 = 42`, `OFF5 = 54`; chapter 1 lives at `OFF6 = 200` (L285).
  They exist because scenes were inserted between older builders' output. The port bakes them into world positions
  (they never reach Unity code).
- **Module names lag scene numbers.** `buildDL02/updateDL02` = DL-03 (+DL-04 reveal), `DL03` = DL-06/07, `DL04` =
  DL-08 and DL-09's tunnel and balcony, `DL05` = DL-11, `Ch1` = the chapter 1 rework helpers used by every prologue
  scene, `Att`/`Att2`/`Att3` = DL-12–14 / DL-15–17 / DL-14a, 14b, 16a and DL-17's rig (README L79–91, L145–204).

### 0.2 Coordinates and units

| Space | x | y | z | Notes |
|---|---|---|---|---|
| Blender (`art/`) | lane, + right | + into the set (behind the lane) | up | `chapter1_build_spec.md` §1 |
| three.js (prototype) | lane | up | − into the set; camera at +z | `(x, z, −y)` of Blender (L266) |
| **Unity (target)** | lane, + right | up | **+ into the set; camera at −z** | `Unity = (three.x, three.y, −three.z) = (Blender.x, Blender.z, Blender.y)` |

- Metres throughout; D-17 is 0.71 m tall. The lane is z = 0. Every gameplay coordinate in Core is `(x, y)` on the lane
  plus an optional depth `z` used only by acts that step into the set (levers, secret rooms, curios).
- Every three.js `z` quoted below must be negated for Unity. Example: `PAWL_Z = -0.3` (L3010) → Unity z = +0.3.
- **U-12 must verify** with a test GLB that glTFast's handedness conversion delivers this mapping (glTFast and
  three.js's `GLTFLoader` do not convert identically); if not, the importer applies one root transform per set.
- Clip time: clips are authored at **24 fps** (`FPS = 24`, L268); code compares clip frames (`actions.X.time * FPS`).

### 0.3 Regions and scenes in the prototype

The prototype is one lane. `game.region` (1–6) selects collision, interactions, lights and camera code; scene names
are derived from x (`sceneName`, L8135–8144).

| Region | World x | Scenes | Region change |
|---|---|---|---|
| 1 | −0.3 → 11.45 (`LEFT_LIMIT`, `RIGHT_LIMIT`, L303) | DL-01 | `transit` stage 2 → region 2 (L2150) |
| 2 | 12.2 → 60.3 (`SH.x0+0.2` → `REGION3_X = OFF3+27.3`, L2457) | DL-02, DL-03, DL-04, DL-05 | x > 60.3 → 3 (L2042) |
| 3 | 60.3 → 80.75 (`REGION4_X = OFF3+47.75`, L3007) | DL-06, DL-07 (`game.upper` = on the gallery) | upper and x > 80.75 → 4 (L2044) |
| 4 | 80.75 → 127.9 (`REGION5_X = OFF5+73.9`, L3446) | DL-08, DL-09, DL-10 | x > 127.9 → 5 (L2047) |
| 5 | 127.9 → 170.9 (`END5_X + 0.8`, L1767) | DL-11 and the prologue ending | exit (L3684) |
| 6 | 200.3 → 342.4 (`ATT.x0/x1`, L294) | DL-12 … DL-17 (incl. 14a, 14b, 16a) | loaded on demand (L5129) |

---

## 1. Locked decisions (not re-debated here)

Unity 6 LTS `6000.3.x` (the skeleton pins `6000.3.0f1`), URP 17.0.3, project `unity/DeadLetter/`. Packages already in
`Packages/manifest.json`: Input System 1.14.0, Cinemachine 3.1.2, Timeline 1.8.7, glTFast 6.8.0, Test Framework 1.4.5.
Assemblies `DeadLetter.Core` (`noEngineReferences: true`), `DeadLetter.Runtime`, `DeadLetter.Editor`; Core is also
compiled by `unity/core-tests` (dotnet 8 + xUnit). Platforms Steam, Itch, Switch (720p handheld / 30 fps target;
IL2CPP/AOT safe). Blender Python generators under `art/` stay the art source of truth. Platform services behind
`IPlatformServices` / `ISaveStore`.

---

## 2. Assembly, namespace and folder layout

Root: `unity/DeadLetter/Assets/DeadLetter/`. Existing: `Core/DeadLetter.Core.asmdef`, `Core/Simulation/FixedTick.cs`,
`Runtime/DeadLetter.Runtime.asmdef` (root namespace currently `DeadLetter`; set it to `DeadLetter.Runtime`),
`Editor/DeadLetter.Editor.asmdef`, `Tests/EditMode`, `Tests/PlayMode`.

```
Assets/DeadLetter/
  Core/                         DeadLetter.Core.*          pure C#, no UnityEngine, no LINQ in per-tick paths
    Simulation/                 FixedTick (exists), SimClock, SimRng (seeded xorshift; replaces every Math.random),
                                StepPipeline (the L8491 order), WorldState, ISimSystem
    Maths/                      Vec2, Vec3 (blittable), Smooth (smoothstep L1527), Damp (exact exponential), Keyed (L6760)
    Lane/                       LaneGeometry (floorAt/surfaceAt/supportAt/ceilingAt/limits), Box1D, Ramp, ILaneContributor
    Motor/                      MotorTuning, MotorState, KinematicMotor, MantleProfile, HoldMotor, PaceRules
    Interaction/                InteractionResolver, InteractionCategory, Candidate, OverlapAudit, ActRunner, IAct,
                                Acts/ (Approach, Turn, StepIn, Lift, SetDown, Grab, Lever, Crank, Present, Sit, Hide, ...)
    Carry/                      CarriedItem, ItemState, PlaceSearch (never-refuse set-down, L4342)
    Push/                       Pushable, PushTwin, TipIntoPit, Detents
    Mechanisms/                 IMechanism, MechanismId, MechanismGraph, Signals (Load, Engaged, Position)
      Plates/                   LoadPlate, WeighScale (banded reading), PresenceStrip
      Actuators/                FollowerActuator (rise slow / fall fast / slam), CrankActuator (n strokes), Door
      Catches/                  Latch, Pawl (bite window), CageCatch, CycleBrake
      Lifts/                    CounterweightLift (pan-driven), SlippingCage, RelocationLift, PupilLift, Dumbwaiter, CounterweightRack
      Drives/                   PairedBlindDrive (clutch/jam), PulseSequencer (relays)
      Routes/                   CarrierLine (routes, dock, junction, tip), ReturnsBelt, PointsLever
      Water/                    SluiceRig (tank, sluices, beds, float latch), Flood
      Cycles/                   CycleClock (lesson dial, night-light)
    Beings/                     WhiteBrain, WaterBody, NoiseEvent, EscortTrolley (rail patrol; attendant precursor)
    Hazards/                    PeriodicCrusher (press), ArcCable, Sump, Collapse, DeathRules
    Cues/                       CueClock (moment time), MomentTimeline, KeyShot, MusicDirectorModel, AmbienceRules
    Camera/                     FramingVolume, FramingTrack (frameFor math), ShotSelector (currentShot rules), ShakeModel
    Hints/                      HintRules, HeadLookLimits, GlintSweep, Pips
    Save/                       SaveModel, CheckpointOrder, CheckpointDef, PersistFlags, CollectionState
    Story/                      Letters, Curiosities, SecretRooms, VoiceCards, Tannoys (placement + state, no audio)
    Telemetry/                  EventLog, EventType, Summary
    Scenes/                     SceneDef DTOs + bespoke rule classes (WeighIn05, Lesson13, NightLight14a, Rig17, ...)
  Runtime/                      DeadLetter.Runtime.*       thin MonoBehaviours
    Boot/                       BootLoader, ShaderWarmup, StreamingDirector, PersistentRoot
    Sim/                        SimDriver (FixedTick → StepPipeline, interpolation), InputBridge (Input System → InputFrame)
    Player/                     D17View (Animator + root placement), ClipClockBridge, HeadLookRig, AntennaBend, LabelStamp
    Mechanisms/                 MechanismView base + one view per Core type (moves transforms, swaps emissives)
    Beings/                     WhiteView, EscortTrolleyView, RipplePool
    Camera/                     LaneCameraRig (Cinemachine 3), ShotDirector, MomentPlayer (Timeline driven by cue clock)
    Lighting/                   LightProxy, LightPool, LightZoneSwitch, EmissiveDriver, CanvasDisplay (screens, boards)
    FX/                         SparkPool, SteamPuffs, DustField, Drips, LightShafts
    Audio/                      SfxBank, MusicDirector (dspTime cue clock), VoicePlayer (treatment chain), AmbientEmitters
    UI/                         TitleCard, PauseCard, EndCard, Intertitle, LetterReader, KeyCap, Subtitles, TouchPad
    Platform/                   IPlatformServices, ISaveStore, SteamPlatform, ItchPlatform, SwitchPlatform (stub), Settings
    Debug/                      DevOverlay (the ` overlay, L8485), ReplayRecorder
  Editor/                       DeadLetter.Editor.*
    Import/                     GlbPostprocessor (glTFast), NameConventions (COL_/LGT_/MECH_/CAM_/CHK_), ClipTableBuilder
    Builders/                   SceneBuilder (SceneDef → DL-xx.unity), LightBuilder, ColliderBuilder, StaticBatcher
    Validation/                 OverlapAuditWindow (auditNear in the editor), SceneDefValidator, BudgetReport
    Bake/                       SfxBaker (offline render of the synthesized SFX, §4.23), WornMaterialBaker (§4.3)
  Tests/
    EditMode/  PlayMode/        Unity Test Framework; PlayMode replays recorded inputs per scene (U-18)
unity/core-tests/               dotnet xUnit project compiling Core/**.cs directly (exists)
Assets/Art/<scene>/             imported GLBs + generated prefabs   Assets/Scenes/  generated .unity files
Assets/Audio/                   music (from game/undelivered/assets/music), baked SFX, voice
Assets/Settings/                URP assets per tier, Input actions, quality tiers
```

**Rules.** Core owns all gameplay state and time. Runtime never decides an outcome; it reads Core state each rendered
frame and writes transforms, materials, audio. Editor turns art and data into scenes; nothing in a `.unity` file is
hand-placed except what a builder regenerates.

---

## 3. Runtime architecture

### 3.1 The step

The prototype advances with a variable `dt` clamped to 0.05 s (L8467–8469) and, under `window.__sim`, a fixed 60 Hz
(L8470–8478). **The port uses a fixed 60 Hz Core step everywhere** (`FixedTick`, already in Core), with render
interpolation; at 30 fps two steps run per frame. All the prototype's `x += (target − x) * min(1, dt * k)` easings are
frame-rate dependent; Core reimplements them as exact exponential damping (`Damp(x, target, k, dt)`) tuned to match the
60 Hz behaviour, so the replay harness and the web sim agree.

`step(dt)` order (L8491–8528), to be preserved by `StepPipeline`:

| # | Prototype call | Core system |
|---|---|---|
| 1 | `game.clock += dt`; respawn when `respawnAt` passes (L8493–8494) | SimClock, RespawnRule |
| 2 | `pollGamepad` (L8495) | InputFrame (from Runtime) |
| 3 | opening: `CUES` timeline, grit, end at frame 480 (L8503–8507) | OpeningTimeline |
| 4 | `updatePlayer` (L1931) incl. acts, holds, rides, triggers | Motor + ActRunner + Triggers |
| 5 | relay pulse every 144 frames (L8511–8516) | PulseSequencer |
| 6 | `updateMechanisms` (DL-01 shutter/chain), `updateAtmosphere`, `updateDL02` | Mechanisms (all, below) |
| 7 | play only: `updateDL03`, `updateDL04`, `updateDL05`, `updateCh1`, `updateAtt`, `updateRingC`, `updateHazards`, `updateClockHands` (L8518) | Mechanisms, Hazards |
| 8 | `updateSparks`, `updateCurios`, `Glints.update`, `Pips.update`, `updateAmbience`, `updateWhite` (L8518) | FX, Hints, Cues, Beings |
| 9 | `syncRide` (carriers move after the player, L2959–2964) | RideSync (must run after mechanisms) |
| 10 | `updateCharacter` (yaw, antenna, head look, key cap), `placeWeight`, `updateQuirkTriggers`, `applyLights`, `updateCamera` (L8520–8524) | Presentation (Runtime) reading Core |
| 11 | `Ambience.update`, `Voice.update`, `updateTannoys` (L8525) | Audio rules |
| 12 | clear edge-triggered input (`jumpPressed`, `usePressed`, L8527) | InputFrame consume |

### 3.2 State

`game` (L1282–1305) is one mutable object with ~150 fields plus per-scene sub-objects (`game.ch1` L4093, `game.att`
L5230, `game.dl4`, `game.dl5`). The port splits it into `WorldState` components keyed by `MechanismId` and a
`PlayerState`. Each scene's reset-from-checkpoint function (`resetWorld` L8015, `resetCh1` L4091, `resetAtt`/`2`/`3`
L5228/5538/5912) becomes a per-mechanism `ResetFor(CheckpointId)` that reads the checkpoint's solved flags (§4.28).

### 3.3 Acts and animation clock

Everything D-17 does that is not free movement is a `game.act = { kind, phase, t, ... }` state machine
(`beginUse` L1817, `updateAct` L1837, `updateActCh1` L4389, `updateAttAct` L5301, `updateAtt3Act` L6015). Phases are
`approach` (walk to `standX` at `WALK*0.8`, L4380–4388) → optional `turn` (yaw to π, into the set) → optional `in`
(step along z at 0.45 m/s) → `act` (a clip; events fire at clip frames, e.g. `Lift` carry starts at f22, done at f39,
L4416–4421) → `out` → null. **The clip frame thresholds are gameplay.** Core therefore owns a `ClipTable`
(clip name → frame count, loop flag) generated by the Editor from `d17.glb` (76 clips, §8) with the `LOOP_FRAMES`
overrides of L315–316 applied, and advances act time itself; the Runtime Animator plays the same clip at the same
normalised time (`ClipClockBridge`) and never feeds events back. This keeps Core deterministic and testable.

### 3.4 What is not in the prototype

| System (full_game_plan §5) | Status in `index.html` | Port action |
|---|---|---|
| Support transfer ("replacement takes the load before the old support is removed") | absent | Design `SupportTransfer` in Core from §5 only; first use DL-19+ |
| Partner ("holds until the other reaches a safe ready state") | absent | Design only |
| The attendant (movement in marked zones) | absent; DL-14b's escort trolley (L6352–6434) is the closest precursor (beam-zone detection, gentle escort, decoy) | Build `EscortTrolley` generically as a zone-sensing rail being; attendant extends it |
| Water as weight | partial: DL-17 beds and float (L6247–6259); no suspended-water weight | `SluiceRig` + a `WaterLoad` term in `LoadPlate` later |

---

## 4. System map of `index.html`

Each section: lines, behaviour, tuned constants (value, line), Unity target. "Core:" = `DeadLetter.Core` class,
"Runtime:" = MonoBehaviour, "Editor:" = builder/importer.

### 4.1 Boot, loading, warm-up

**Lines:** L1313–1455 (loader, `prepare`, `load`), L5128–5137 (`loadAttendance`), L8599–8615 (`warmUp`),
L8616–8632 (`boot`). **Behaviour:** models ship as base64 GLB in JSON parts (`set.json` + 4 parts, `attendance.json`
+ 2) decoded into one buffer (L1324–1351). `load()` fetches `set`, `d17`, `couriers` in parallel, then `white`
before Begin (L1445), then builds every scene's runtime objects (L1433–1453). `prepare()` swaps materials by name and
sets shadow flags: only skinned meshes and props < 3.2 m across inside `SHADOW_ZONES` cast (L1356–1362). `warmUp()`
uploads every texture and compiles every material once per region light configuration **into the composer's render
target** (L8610–8612), because compiling for the screen built unused variants (README L23–28). Chapter 1's set loads
on first need and compiles the same way (L5133).

| Constant | Value | Line |
|---|---|---|
| Base64 part size | 10,000,000 chars | L1342 |
| `SHADOW_ZONES` | [−2.5, 7.0], [26.8, 31.4], [81.4, 89.0] | L1356 |
| Shadow caster max size | 3.2 m (bounding-box diagonal) | L1361 |
| Warm-up configurations | (r1), (r2), (r2, ration), (r3), (r3 upper), (r4 upper), (r4 upper, uo), (r5 upper) | L8611 |
| Shader programs after pool | 54 (247 before), 3 compiled during the opening | README L27–28 |

**Unity:** Editor imports GLBs at edit time (no runtime glTF parsing; glTFast stays an editor/import dependency).
Runtime `BootLoader` loads the persistent scene, then `ShaderWarmup` runs a `ShaderVariantCollection` per quality tier
(collected by playing every scene with the replay harness) plus `GraphicsStateCollection` on Unity 6 where supported.
Loading chapter 1 becomes an additive scene load (§7).

### 4.2 Renderer and post

**Lines:** L338–381. **Behaviour:** no MSAA; adaptive pixel ratio; AgX tone mapping; exp² fog per camera volume;
bloom at half resolution; a final grain + vignette + fade pass.

| Constant | Value | Line |
|---|---|---|
| Pixel ratio | start `min(dpr, 1.0)`, min 0.6, max `min(dpr, 1.5)` (1.25 touch) | L342 |
| Adaptive step | every 2 s: fps < 46 → −0.15; fps > 58 → +0.1 | L8455–8465 |
| Tone mapping | AgX, exposure 1.4 × brightness (0.8–1.8) | L344–345, L8307–8313 |
| Shadow map type | PCF (soft PCF cost a third of the frame) | L346–347 |
| Background / fog | `0x030404` / FogExp2 `0x040505`, density 0.075 (overridden per frame by framing volume) | L350–351, L7797 |
| Camera | fov 40 initial, near 0.05, far 60 (60 + 340·vista in the atrium), filmGauge 36, base focal 35 mm | L352–353, L3257, L7805 |
| Bloom | strength 0.55 (calm 0.35), radius 0.5, threshold 0.92, rendered at half size | L357, L8290, L377 |
| Grain/vignette | noise ±0.0175 (`*0.035`), vignette `mix(0.55, 1, smoothstep(0.85, 0.2, r))`, `uFade` multiplier | L360–369 |

**Unity (U-15):** URP Forward on Switch, Forward+ on PC; Volume profile per tier: Bloom (half/quarter res on Switch),
Film Grain (off on handheld), Vignette, Tonemapping via a custom 3D LUT exported from Blender's AgX view (URP has no
AgX; do not substitute ACES without the director). Fog: URP exponential-squared fog, density driven per frame by
`FramingTrack`. Dynamic resolution (`ScalableBufferManager` / URP render scale) replaces the DPR stepper with the same
thresholds scaled to 30 fps (step down below 28, up above 31 for 2 s).

### 4.3 Materials and the worn shader

**Lines:** L383–554 (`NOISE`, `WORN`, `PLAIN`, `GLASSY`, `EMIT`, `wornMaterial`, `materialFor`), L2163–2170
(`plainCourier`), L4028–4043 (DL-05 body sheet ripple), L7066–7087 (`whiteMaterial`).
**Behaviour:** materials are matched **by Blender material name** (`.001` suffix stripped, L528):
- `WORN` (64 entries, L393–458): `MeshStandardMaterial` + one shared shader patch (`customProgramCacheKey 'worn'`): object-space
  fbm (3 octaves of value noise) blends base → dirt (grime/streak masks) → chipped paint (roughness override) → dust on
  up-facing normals (L493–523). Parameters per entry: `base, dirt, chip, rough, chipRough, metal, grime, chipScale,
  chipAmt, dust, dustAmt, streak`.
- `PLAIN` (33 entries, L459–467): flat colour/roughness/metal; `Water` becomes transparent 0.66 opacity, roughness 0.24 (L535).
- `GLASSY` (2, L468), `AtriumMist` additive (L538–539), `EMIT` (107 emissive names with colour and default intensity,
  L469–490; the game drives most of them by name through `emissive[name]`).
- Images keep their map; `Chalk*`/`RingLetter*` are alpha decals with polygon offset −2 (L545–548).
- Background couriers get a plain dusty material and dark lamps (L2163–2170, L2200).
- The White: pale skin with rim light and a pink transmission term (L7068–7087).

**Unity (U-12/U-15):** an Editor `MaterialMap` asset keyed by the same names, generated from these tables (copy them
verbatim into `Assets/Settings/MaterialMap.json`). Two options for `WORN`, a director decision (§10): (a) a URP Shader
Graph/HLSL "Worn" lit shader porting L386–391 and L509–519 one-to-one (one variant, SRP-batcher compatible, parameters
in a per-material CBUFFER), or (b) `WornMaterialBaker` bakes the masks to textures in Blender per object. Recommendation:
(a) on PC, (b) on Switch (per-pixel fbm ×3 is ~100 ALU per pixel). `EMIT` → URP Lit emission with an `EmissiveDriver`
that sets intensity through a `MaterialPropertyBlock` (no material instancing at runtime).

### 4.4 Input

**Lines:** L1213–1277; options L8282–8304. **Behaviour:** held keys are a set per source (keys, touch, pad) so releasing
one of two keys keeps him moving; focus loss clears all (L1218–1230). Gamepad: stick deadzone, D-pad overrides, A jump,
X use, B/RB walk, Menu pause. `input.lastActivity` feeds idle hints. Held Use (`useHeld`) drives DL-16's lever.

| Constant | Value | Line |
|---|---|---|
| Keys | A/D/←/→ move; Space/W/↑ jump; E/Enter use; Shift walk(or run); Esc/P pause; R checkpoint; \` overlay | L1217, L1231–1236 |
| Stick deadzone | 0.22 | L1266 |
| Run threshold (stick) | \|axis\| > 0.65 (with auto-run) | L1927 |
| Pad buttons | 0 jump, 2 use, 1 or 5 walk-modifier, 9 pause, 14/15 D-pad | L1267–1275 |
| Auto-run default | on; Shift/B inverts | L8283, L1921–1929 |

**Unity (U-17):** Input System action map `Gameplay {Move (1D axis), Jump, Use (press + hold), Walk, Pause, Checkpoint}`,
`UI`, `Debug`; `InputBridge` writes an `InputFrame { axis, jumpPressed, jumpHeld, usePressed, useHeld, walkHeld }` per
Core step (edge events latched until consumed, L8527). Rebinding and Switch Joy-Con single/dual layouts in U-17.

### 4.5 World state and flow

**Lines:** L1282–1311 (`game`, `refs`, `seen`, `once`), L7968–8133 (title, opening, play, pause, end), L8467–8528
(loop). **Modes:** `title → card → opening → play ⇄ paused → end`. The opening card holds 9.5 s or any key after 1.2 s
(L8073–8074; README says 12.5 s, the code says 9.5), then the 480-frame wake (20 s at 24 fps, `OPENING_FRAMES` L269)
with Skip after 1.5 s (L8070). `seen`/`once()` (L1309–1310) mark authored moments already played so a checkpoint replay
skips them.

**Unity:** `GameFlow` state machine in Core (`Mode`, `SeenMoments` as a `HashSet<string>` saved with the run); UI in
Runtime. Keep the moment keys verbatim (`realise`, `awe`, `hopscotch`, `knock`, `marks`, `bayTouch`, `labelWake`,
`label5`, `label9`, `label11`, `bodyGrab`, `uoBuzz`).

### 4.6 Lane collision (floor, surface, ceiling, walls)

**Lines:** L1617–1643 (`ceilingAt`, shutter path), L1709–1769 (`floorAt`, `surfaceAt`, `supportAt`, `ledgeAhead`,
`leftLimit/rightLimit`), L4135–4201 (`floorCh1`, `surfaceCh1`, `ceilingCh1`, `limitsCh1`), L5244–5273, L5586–5614,
L5940–5971 (chapter 1 equivalents), L6351 (`onRamp`). **Behaviour:** collision is a 1-D height field along x, not
physics: `floorAt(x)` (the ground), `surfaceAt(x)` (max of floor and anything standable there: crates, trolleys,
carried items set down, bunks, steps that exist only for someone already above the level below, L5256–5264),
`supportAt(x)` = max over ±`FOOT` (L1737), `ceilingAt(x)` (shutter polygon, gate, hatches, barricade), and per-region
`[lo, hi]` walls that open and close with mechanism state (gate, bay door, cage shaft, service door, attendance gate,
class door, DL-14a door, DL-16a gate). Dynamic contributors register by region.

| Constant | Value | Line |
|---|---|---|
| `HALF` (body half-width) | 0.17 | L310 |
| `FOOT` (support probe) | 0.08 | L310 |
| `STEP_UP` (walk-up step) | 0.07; on ramps 0.45 | L310, L2004 |
| `STAND_H` / `CROUCH_H` / `ANTENNA_TOP` | 0.76 / 0.58 / 1.12 | L309 |
| Shutter path (closed) | (0.2,1.6) (2.0,0.62) (3.2,0.6) (3.4,0.02), pivot (0.2,1.6), opens 15° | L275–277 |
| Gate blocks below | `gate.y < CROUCH_H + 0.02` | L1750 |
| Ring C barricade | x 134.2–135.0, gap 0.62 | L3462, L1626 |
| Region 6 ceiling | 3.4 everywhere | L1625 |

**Unity (U-10/U-11):** Core `LaneGeometry` composed of `ILaneContributor`s (static boxes from `COL_` meshes, ramps,
dynamic contributors owned by mechanisms). No Unity physics for the hero. `COL_` boxes are authored in Blender as
axis-aligned boxes on the lane (x0, x1, top, optional "only from above y" flag for the boards-in-the-air case) and
exported to the scene definition (§6), not as MeshColliders.

### 4.7 Motor: walk, run, crouch, jump, mantle, fall

**Lines:** L304–316 (constants), L1906–1919 (`startMantle`, `mantleAt`), L1921–1929 (`wantsRun`), L1931–2067
(`updatePlayer`), L2069–2075 (`stepSounds`). **Behaviour:** kinematic, plane-constrained. Auto-crouch from ceiling
clearance; jump with coyote time and buffer; a jump input next to a 0.24–0.62 ledge becomes a 2.33 s authored mantle
(root follows `MANTLE_KEYS`); mid-air ledge catch up to `MANTLE_MAX + 0.1`; landing timers, shake and White noise
from real drops; slope snap; a `Fall` clip for real drops.

| Constant | Value | Line |
|---|---|---|
| `WALK` / `RUN` / `CROUCH_WALK` | 0.9 / 1.6 / 0.5 m/s | L304 |
| Clip authored speeds | Walk 0.79, Run 1.52, CrouchWalk 0.49; CarryWalk 0.295, PushWalk 0.45, SadWalk 0.387 | L305, L326 |
| `SLOW_WALK` / `REVEAL_WALK` | 0.39 / 0.65 m/s (emotional beats) | L327 |
| Acceleration | ground run 6, ground walk 4.5, air 2.2 m/s² ; release friction `vx *= 1 − 10·dt` | L1982, L1984 |
| Stick scaling | `target = sign·top·min(1, \|move\|·1.15)` | L1981 |
| `GRAVITY` / `JUMP_APEX` | 9.8 m/s² / 0.4 m → `JUMP_V = √(2·9.8·0.4)` = 2.80 m/s | L306–307 |
| `COYOTE` / `JUMP_BUFFER` | 0.10 s / 0.12 s | L308 |
| Auto-crouch | crouch when clearance < 0.8; stand when > 0.85 | L1975–1976 |
| Air/crouch ceiling block | `minCeiling − y < CROUCH_H` blocks x | L2007–2009 |
| `MANTLE_MIN` / `MANTLE_MAX` | 0.24 / 0.62 m (standing); airborne up to 0.72 (`+0.1`) with `vy < 1.2` | L310, L2022 |
| Standing mantle trigger | ledge within 0.5 m, `dist < FACE_D + 0.3` (0.47), `FACE_D = 0.17` | L1989–1990 |
| `MANTLE_KEYS` (frame, forward, up-fraction) | (0,0,0) (6,0,0) (10,.03,.12) (14,.03,.18) (20,.05,.45) (24,.05,.38) (32,.10,.78) (38,.20,.95) (44,.33,1) (56,.38,1) | L311–312 |
| `MANTLE_FRAMES` | 56 (2.33 s) | L313 |
| Landing | fall > 0.25 → land timer 0.30 s else 0.18; shake 0.25 if > 0.3; noise 1.1 to the White if > 0.25 | L2024–2028 |
| Slope snap | stay grounded if `0 < y − support < 0.09` | L2031 |
| Fall clip | `vy < −1.4` and drop > 0.25 | L2019 |
| Run clip threshold | speed > 1.15 | L2060 |
| Yaw turn rate | 8 rad/s toward ±π/2 or override | L7579–7583 |
| Careful near White water | no auto-run within 2.0 m of `hunt`/`scare` water | L1925–1926 |
| Light carry | coat, pole, tin, gown: normal walk, can jump and mantle | L1967–1970, L2326–2329 |

**Unity (U-11):** Core `KinematicMotor` + `MotorTuning` (ScriptableObject wrapping a Core POCO with exactly these
fields). Runtime `D17View` places the root and drives an Animator whose locomotion blend uses the clip speeds above
(timeScale = speed / clip speed, L2057–2061). Antenna bend under ceilings (L7591–7598, 70° max over 0.35 m overlap) is a
Runtime bone post-process.

### 4.8 Pace, transits and exits

**Lines:** L2077–2083 (`paceSlow`), L2085–2127 (`updateExit`, `updateEnd5`), L2129–2157 (`TRANSIT`), L5633–5653 (DL-14
duct), L4496–4510 (DL-07 slide). **Behaviour:** scripted locomotion that keeps the camera continuous: DL-01's door
leads into a passage behind the wall (z −1.25) and out at x 13.2 (four legs, yaw-turn then walk at `WALK*0.85`);
DL-14's hatch duct (`ATT2.duct` x 239.7 → 248.95, height 2.15 → 1.15, z −1.3, 1.9 m/s); DL-07's parcel slide (13
polyline points, gravity along slope, speed clamp 0.5–3.0 m/s); the endings (walk out; the prologue's look-up phase
on the `window` cue clock, label at 13.6 s, stair rise 0.714, finish 2.4 s later).

| Constant | Value | Line |
|---|---|---|
| Slow zones | DL-04 kin walk to `KIN_UNTIL_X` 36.6; DL-06 reveal to `REVEAL_STOP_X` 68.9; DL-09 after awe from 112 to 116.55 | L327, L2078–2083 |
| `PASSAGE_Z` / `EMERGE_X` | −1.25 / 13.2 | L319 |
| End walk | DL-08/09 region `SLOW_WALK·1.4`; others `WALK·0.8`; finish after 0.9 s | L2090, L2097 |
| `END5` | lookX 173.2, stairX 174.4, rise 0.714, window (173.6, 24.0, −10.3), cam (172.4, 0.6, 0.8) | L3465–3466 |
| Slide | 13 points from (71.85, 1.6) to (68.70, 0.0); v₀ 0.4, max 3.0, friction 0.6 | L3894–3895, L4499–4508 |

**Unity:** Core `ScriptedPath` acts (polyline + speed law). The transits are why scenes must stream additively with no
cut (§7).

### 4.9 Interaction resolver

**Lines:** L1771–1836 (`NEAR_CATS`, `nearAll`, `auditNear`, `nearUse`, `beginUse`), L4203–4304 (`nearCh1`, `itemsHere`,
`PUSHABLES`, `pushHere`), L5275–5293, L5615–5629, L5974–6002 (chapter 1), region resolvers L2244 (2), L2864 (3),
L3264 (4), L3582 (5). **Behaviour:** "what would Use do here" is a pure query over the player's position, grounded
state, hold and world state, returning a string key (`'lift'`, `'grabPush:courierAlt'`, `'att:sluiceB'`…). Priority
order inside `nearCh1` (L4204–4257): carried item actions → liftable items → curios → secret rooms → voice cards →
fixed controls → letters → pushables (nearest grip wins). Categories `item, curio, secret, voice, letter, push, fixed`
(L1778) can be queried alone; `auditNear` sweeps x in 0.02 m steps on floor and support heights and lists every spot
where two categories answer (L1786–1802); `tools/sim/audit_near.mjs` fails the build if any (README L211–217).
A standing jump (no direction) beside a carrier boards it (L1964–1966).

| Constant | Value | Line |
|---|---|---|
| Item grip offset `GRIP_FWD` | 0.29 m; reach ±0.4 | L320, L4220–4221 |
| Push grips | reach 0.34 (default), cart back 0.2, body-alt fwd 0.06 | L4254, L4274, L4295 |
| Lever / crank / cord reach | 0.38 / 0.36 / 0.22 | L2868, L1814, L1812 |
| Curio reach | `c.r` or 0.24 | L6698 |
| Secret gap reach | open range ± 0.2 | L6603 |
| Voice card reach | 0.22 of `standX` | L6652 |
| Letter / slot reach | 0.42 | L4246–4248 |

**Unity (U-10/U-11):** Core `InteractionResolver` returns a typed `Candidate { Verb, TargetId, Category, StandX,
Face, ZTarget }` instead of strings; each mechanism/item registers `IInteractable` providers with a category and a
priority. `OverlapAudit` is a Core function used by an EditMode test per scene (fails on any overlap) and by the
editor window. The glint sweep (§4.19) reuses it.

### 4.10 Carry and place

**Lines:** L2229–2316 (DL-03 weight: `lift`, `setdown`, `beginSetDown`), L2435–2450 (`placeWeight`), L4259–4272
(`itemsHere`), L4337–4354, L4415–4428 (`liftItem`, `setdownItem`), L4429–4458 (`loadTray`, `loadCarrier`),
L4956–4976 (`placeItem`), L5494–5511, L6327–6345 (chapter 1 placers). **Behaviour:** approach to `x ∓ GRIP_FWD`,
`Lift` clip (sound f13, attach f22 blended over 4 frames, carrying at f39), `CarryIdle/CarryWalk` at 0.42 m/s, no
running or jumping (heavy items). Set-down **never refuses** (pass 3): tries `GRIP_FWD`, +0.08, +0.16, −0.05 in front,
then behind, then in front anyway (L4342–4353); the item drops over 0.2 s. Context set-downs: onto the trolley deck
(`SetDownHigh`), into a carrier (two weights shift ±0.14), into the counterweight tray, into the lift car, onto pegs
and hooks.

| Constant | Value | Line |
|---|---|---|
| `CARRY_WALK` | 0.42 m/s | L325 |
| Lift clip events | f13 sound, f22 attach (+4 f blend), f39 carry | L4418–4420 |
| SetDown events | f14 release, f35 done | L4425–4426 |
| Item hang below wrists | `BAIL_BELOW_WRIST` 0.28 (weights, plates, box); case 0.24; coat 0.16; pole 0.08; tray 0.12; gown/bag 0.02 | L320, L4261–4268, L5928–5929 |
| Weight (DL-03) | r 0.10, h 0.22 | L320 |

**Unity:** Core `CarriedItem` with `ItemState { Floor, Carried, Placed(slot), InCarrier, Gone, Tumble }`, `PlaceSearch`;
Runtime attaches the item's transform between the wrist bones `ik_handL/ik_handR` (L1423) minus `below`.
*Built (#22):* `Mechanisms/Loose/Carryable` (`Rest`, `Carried`, `OnDeck`, `Placed`; an `IPlateBody`), decks via
`Loose/PushableDeck`; carriers keep their own load codes. Tumble and Gone are not ported yet.

### 4.11 Push, pull, drag, tip

**Lines:** L2318–2362 (`updateHold`: DL-03 trolley, DL-08 goods trolley, DL-11 desk), L4273–4304 (`PUSHABLES`, twins),
L4683–4749 (`updateHoldCh1`, `teeter`, `tipOver`, `tipInto`), L5536–5585, L6449–6459 (chapter 1 pushables).
**Behaviour:** grab from a stand point `x − side·gap`; the object follows his hands within `[min, max()]`; Jump or Use
lets go. Pass 10 made most pushables two-sided ("twins" share state, L4287–4295). Things with `detent` stop at the next
detent and release (L4718–4722). The cart and duct stop teetering at a pit lip; holding into the lip for 0.45 s, or
letting go there, tips them in (0.9 s nose-dip slide, L4742–4749). At the end of travel: courier → cradle, drum → set,
body → plate (+pat quirk after 1.6 s).

| Pushable | side | gap | speed m/s | min → max | Line |
|---|---|---|---|---|---|
| DL-03 trolley | ±1 | 0.62 (`PUSH_GAP`) | 0.55, 0.42 loaded | 25.44 → 30.0 (stops against the weight) | L321–325, L2341–2346 |
| DL-08 goods trolley | ±1 | 0.70 | 0.34 (`PUSH_HEAVY`), acc 1.3 | 81.95 → 84.5; latched: to `RAIL7.x0 − 0.38` | L3008–3009, L2341 |
| DL-11 desk | +1 | 0.90 | 0.26 (`DRAG_SPEED`) | 166.45 → 167.6 | L3469 |
| DL-01 cart | +1 (back 0.2) | 0.97 | 0.55 | 5.9 → 6.33 (lip) | L4274 |
| DL-04 courier (+Alt) | −1/+1 | 0.67 | 0.22 | 41.2 → 44.5 | L4275 |
| DL-05 drum (+Alt) | +1/−1 | 0.55 | 0.30 | 53.45 → 54.80, then → 56.02 | L4277 |
| DL-05 body (+Alt) | −1/+1 | 1.05 | 0.20 | 52.30 → 54.80 (blocked by drum) | L4279–4281 |
| DL-11 duct | +1 | 1.10 | 0.45 | 148.0 → 148.75 (lip) | L4285, L3903 |
| DL-12 fig (+Alt) | +1/−1 | 0.6 | 0.40 | 206.65 → 208.4 | L4283 |
| DL-13 fig2 (+Alt) | +1/−1 | 0.6 | 0.40 | 217.3 → 219.4 | L4284 |
| DL-15 figures A/B (×2 sides) | ±1, detents | 0.6 | 0.35 | `figRange15` (lift, seats 283.2/284.6) | L5537, L5557–5585 |
| DL-14b figure (×2) | ±1 | 0.6 | 0.35 | 261.8 → 275.0 | L6450–6459 |
| DL-16a stool (detent) | ±1 | 0.5 | 0.40 | 310.45 → 312.2 | L6455–6458 |

| Constant | Value | Line |
|---|---|---|
| Hold acceleration | 1.4 (chapter 1 pushables); light 3, heavy 1.3 (old holds) | L4690, L2332 |
| Shove into lip | 0.45 s | L4709–4710 |
| Teeter | nose −0.07 ± 0.015·sin(7t) | L4738 |
| First body grab hesitation | 1.6 s | L4463–4466 |

**Unity:** Core `Pushable` (data: side, gap, speed, min, max delegate, detents, tipsIntoPit) + `PushTwin`; the hold
motor is part of `KinematicMotor`. Clips `Grab`, `PushIdle`, `PushWalk` (signed timeScale for pulling).
*Built (#22):* `Mechanisms/Loose/Pushable` (twin, deck, blockers, loaded speed, `Accel`, `LetGoAtMax`, done at max);
the pit-tippers stay `Bridges/TippingBridge`.

### 4.12 Other verbs: present, sit, hide, knock, levers, cranks, buttons

**Lines:** L1837–1901 (DL-01 cord, latch, crank), L2895–2958 (levers, board, alight), L3289–3397 (pawl, teeter, pat,
hopscotch, look-back, awe), L3601–3670 (present, toy, knock), L4527–4608 (DL-10 buttons, crank, ride), L5673–5684
(DL-15 sit), L5685–5694 (DL-16 held lever), L6111–6135 (DL-14b hide, escorted).

| Verb | Clip and timing | Line |
|---|---|---|
| Cord (DL-01) | `Tug`; click at f19; done f43 | L1862–1869 |
| Latch (DL-01) | crouch, `Pull`; lever keys (0,0)(12,0)(20,12)(24,8)(30,22)(33,70)(40,72)°; release at f31; `Flinch` f39 for 1.6 s | L1645–1650, L1870–1876 |
| Crank (DL-01 door) | turn to π, `Crank` loop (24 f), 5 strokes × 60°, door rises 1/5 per stroke | L299, L1877–1897 |
| Lever (DL-06 stop/points) | turn, step in to z = `LEVER_Z + 0.26`; `LeverPull` throw at f22 (angles −18° ↔ 6°), out at f33; `LeverStuck` when points are thrown with the belt running (2 clunks, f45) | L2460, L2899–2937 |
| Board / alight carrier | `Hop` take-off f8, land f18, done f23, arc 0.38 m | L2884–2894 |
| Pawl (DL-08) | `LeverPull` bites at f22 only if platform h ≥ 0.985; else `LeverStuck` (dog rattles, dips 0.45) | L3290–3324 |
| Present (DL-11) | turn, step in to z = −0.7; `Present`: lamps f20/25/30, NOBODY f36, FORWARD + label stamp f50, out f63 | L3603–3625 |
| Knock (DL-11) | step to z 0.07, `Knock` taps f14, f20; wait 1.9 s; 3 cm step; `Tug` cord, door at f19 | L3634–3668 |
| Up buttons (DL-10) | `PressButtonHigh` press window f13–22, act at f16, done f34 | L4579–4597 |
| Service crank (DL-10) | 4 strokes; any move > 0.3 after 0.5 s stops cranking (door holds) | L4565–4577 |
| Sit (DL-15) | `Sit` → `SitIdle` after 0.66 s; seated flag after 0.4 s; move after 1.0 s → `SitUp` 0.6 s | L5673–5684 |
| Held lever (DL-16) | held while Use is held (`useHeld`) after 0.25 s; release or move lets it spring back | L5685–5694 |
| Hide (DL-14b) | step back to z −0.62, crouch; any input after 0.3 s steps out | L6111–6125 |

**Unity:** one `IAct` per verb in Core (`Acts/`), parameterised by a `VerbProfile` asset (clip, event frames, stand z).
*Built (#22):* the acts live in `D17Motor`; a station answers `Offer(query) → StationPose` and `ProfileFor(query)`
(asked again after step-in) and each frame an `ActStep` (continue, done, a chained clip, a hop). Hide is `IHideSpot`,
the escorted walk `IEscort`, board/alight `IRide`; stuck, death and quirks (CheckLabel, Flinch) are motor acts the
scene runner starts.

### 4.13 Mechanisms

Each subsection lists every instance. IDs are proposed (`dlNN.name`) and used in §5 and in save data.

#### 4.13a Load plates and scales

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl01.scale` (curio) | L4767–4769 | needle swings −95° while he stands within 0.22 of x 1.45 | rate `dt·3` |
| `dl03.plate` → `dl03.gate` | L2229–2238, L2365–2433 | load = D-17 1.0 + trolley 0.3 + weight 0.42 (on floor, on trolley or carried); gate height = min(1, load)·1.2; solved when the plate holds ≥ 0.68 **without him** and the gate is at that height | `LOAD` L324, `PASS_LOAD 0.68` L324, `GATE_OPEN_H 1.2` L323, plate x 28.8–29.55 L323, gate x 30.6 |
| `dl04.bayPlate` → `dl04.bayDoor` | L4783–4822 | D-17 on the plate (44.0–45.0) or the seated courier opens the door (1.7 m); opens over 1.1 s (him) / 2.2 s (courier), closes over 0.5 s | `RK` L3890 |
| `dl05.weighIn` → `dl05.hatch` | L4878–4921 | W = body share + 1.7·drum share + 0.2 if he is on; bands: empty < 0.05, UNDER < 0.85, PERSON ≤ 1.15, OVER; PERSON held 1.0 s → served (latched), hatch winds to 0.64 at 0.22 m/s, flag drops 0.5 s | plate 53.85–55.75 L3453; needle −28/−140/−236° L3453; spring k 30, damping 7 L4905; twitch ±22° band, 1.2 s cool-down L4909–4910 |
| `dl08.pan` → `dl08.platform` | L3021–3030, L3171–3207 | pan load = 1.05·(trolley share on pan) + 0.5 (him); platform target h = pan − (0.5 if he stands on the platform) clamped 0–1; latched → 1 | `LOAD4` L3012, `PAN` 83.5–84.9 L3009, `RISE 2.7`, `PLAT_SPEED 0.6` L3011 |
| `dl09.tray` (counterweight) | L5011–5078 | 0, 1 or 2 plates; < 2 → cage dips; gauge needle 48°·plates/2 | `CW8` L3320 |
| `dl10.carPlate` | L4622–4647 | suitcase in the car → gate closes 0.8 s later over 1.4 s; needle and gauge; three sill lamps 0.25 + 0.3i s | `UO` L3459–3461 |
| `dl12.strip` (presence) | L5381–5408 | someone (him, or the figure within 0.25 of 208.4) on the strip 208.0–208.8 AND coat on peg 7 → gate to 1.3 m | `ATT` L286–295 |
| `dl15.seats` | L5726–5736 | figure docked at 283.2 and 284.6 + him seated on Mara's chair (286.0) for 1.6 s → dismissal | `ATT2` L5523 |
| `dl16a.carLoad` | L5935–5938, L6165–6186 | tins in car vs `need` (0 after the redesign): > need → OVER buzz; < need → shoot; = need → rise | `ATT3.weight`, `need: 0` L5904 |

Follower gates (DL-03 gate, DL-12 gate) share one law: **rise at 0.55 m/s (DL-12: 0.5), fall with acceleration 9
(DL-12: 8) up to 3.2 m/s (DL-12: 3), slam sound + shake if v > 0.8 on landing, never onto him** (gate stays above
his head height while he stands under it) (L2380–2392, L5400–5406).
**Unity:** Core `LoadPlate` (sum of weighted shares of registered `ILoad`s over an x-interval), `WeighScale` (banded,
hold-to-latch), `FollowerActuator` (the law above, parameterised).

#### 4.13b Docks and cradles

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl04.cradle` | L4787–4813 | courier let go within 0.6 of 44.5 → arms reach (1.2 s), draw it in, close (0.8 s), seat; lamps flicker 2.2 s then hold; one `TouchHead` act | `RK.bayX 44.5` |
| `dl06.dock` | L2693–2704 | carriers wait at the dock `DOCK_WAIT` 3.4 s while the belt runs; held while he boards | L2461 |
| `dl15.lift`/rail detents | L5535, L5557–5574 | detents at 281.9 (lift), 283.2, 284.6; pushes stop at the next | L5535 |
| `dl16.rack` | L5744–5766 | procession figures roll into the rack at 305.6 and hang on 2 hooks; full → latch 1.2 s later, counterweight lifts 2.0 m over 1.8 s | `ATT2` L5526–5528 |

#### 4.13c Latches, pawls, catches, brakes

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl01.latch` → `dl01.shutter` | L1674–1707 | pull releases: shutter swings to 15° with an overshoot settle over 0.9 s, counterweight falls 0.54 s from 1.56 to 0.12 | L275–280, L1682–1692 |
| `dl08.pawl` | L3122–3126, L3290–3324 | bites only at the landing (h ≥ 0.985); latched platform stays at h = 1 | `PAWL_X 85.45`, `PAWL_REST 1.75` L3010 |
| `dl09.cagePawl` | L5079–5096 | Use while lowering/slipping: bites if cage y ∈ [landing − 0.06, landing + 0.45]; else rattles, re-armed after 0.6 s | L5090–5093 |
| `dl13.brake` | L5344–5363 | toggles `lesson.braked`; freezes the cycle where it is; with no lesson running it only clunks | — |
| `dl14a.brake` | L6078–6082 | toggles the night-light cycle | — |
| `dl16.latch` | L5764 | drops when the rack is full | — |
| `dl17.latch` | L6258–6259, L6314 | bed 1 ≥ 0.95 → latched; latch angle follows 0.7·bed1 before (a shared run lifts it part-way) | — |

**Unity:** Core `Latch` (Locked→Released), `Pawl` (bite window predicate on another mechanism's position),
`CycleBrake`. These are the "Brakes and catches" permanent rule (full_game_plan §5).

#### 4.13d Shutters, doors and gates (actuators)

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl01.door` | L1877–1897, L7957 | crank strokes raise it to `DOOR.h − 0.05` | `DOOR` 10.0–10.8, h 1.05 L300; `CRANK_X 9.62`, 5 strokes L299 |
| `dl05.hatch` | L4915–4921 | served → 0.64 m; twitch 0.14 m when the needle crosses PERSON | `RH5.open 1.2`, `onDrum 0.64` L3454 |
| `dl07.gate` + bucket | L3892, L4825–4837 | gate target = 1.4 m with 2 weights, 0.38·b otherwise (never a crouch gap); rises 0.45 m/s; strain + pips flash when it stalls | `HP` L3893 |
| `dl10.serviceDoor` | L4565–4577, L4654 | 4 crank strokes lift it 1.45 m; holds where left | `UO.strokes 4`, `doorLift 1.45` |
| `dl11.c114Door` | L7274–7289 | cord pulls lever −35°; door opens 95° over 1.6 s (ease-out cubic) | `C114DOOR` L3470 |
| `dl14a.door` | L6227–6228 | opens 1.2 s after the room is dark, over 1.4 s | — |
| `dl15.classDoor` | L5737 | opens over 1.6 s on dismissal | — |
| `dl17.stairDoor` | L5789–5794 | opens 0.8 s after the float latch, over 1.8 s | `ATT2.door17` L5530 |

#### 4.13e Relays and pulse sequencers

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl01.relay` | L1534–1548, L1551–1578, L8511–8516 | lamp i lights from frame `start + 12i` to `start + 30`, then fades over 10 frames; sets start at frames 120 (strength 0.55), 168 and 336, then every 144 frames (6 s) from frame 480 for the rest of the depot; D-17's lamps answer 4 frames later; pulse fades from x 90 (`OFF3+57`) over 7 m | `RELAY_SETS` L332, `SPARKS` L333 |
| `att.relays` (service line) | L5163–5166, L6316–6325 | four green pilot lamps, 7 s cycle each, phases 2.3 s apart; the pump relay blinks while DL-17's tank refills | — |

#### 4.13f Lifts and counterweights

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl08.platform` (Lift 2) | L3171–3261 | rises at 0.6 m/s toward the pan's target; falls with accel 8 up to 3.4 m/s and crashes (v > 0.6); stepping on unlatched → `Teeter` back (platform dips 0.1 m) | `RISE 2.7`, `DECK 1.6`, `SHAFT` 85.8–88.3 L3011 |
| `dl09.cage` | L5011–5096 | see table below | `CG` L3899–3900 |
| `dl10.lift` | L4611–4675 | phases idle → up (5.5 s smoothstep, travel 1.6) → top (3 s) → down; with him on the counterweight: up → gone | `UO.ride 5.5`, `travel 1.6` L3461 |
| `dl15.pupilLift` | L5712–5725 | goes down (0.65 m/s) only with a pupil AND him aboard; back up when empty; buzzes if he rides alone | `ATT2.lift` L5521 |
| `dl16a.dumbwaiter` | L6233–6246 | call down / rise over 4.2 s; too light "shoot" to 1.5 m in 0.8 s, catch bites, lowered by 4.0 s | `ATT3.car` L5903 |
| `dl16.rackCW` | L5766, L5839 | lifts 2.0 m when latched | `ATT2.cw` L5528 |

`dl09.cage` phases (L5020–5050): `top` → (him in, < 2 plates) `dip` 0.38 m (0 plates) / 0.22 m (1 plate) over 0.35 s,
crash + bell, hold to 1.6 s → `haulDip` 0.4 m/s → `top` (needs step out; ready after 0.8 s). With 2 plates:
`settle` 0.04 m over 0.9 s → `lower` 0.32 m/s to top − 0.55 → `shudder` 0.7 s → `slip` (accel 2.6 to 1.6 m/s) → catches
once at landing + 0.35 → `stall` 0.75 s → `slip` (v 0.3) → pawl `bite` (0.5 s to landing) → `caught`; else `crash` at
y −0.1 (death `fall`), hold 1.4 s → `haul` 0.7 m/s → `top` (ready after 1.6 s). Cage top 3.4, landing 1.6.

#### 4.13g Paired outputs and clutch

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl14.blinds` | L5364–5376, L5437–5476 | one crank wind swaps blinds A and B (2.2 s travel); the window pole through A's wheel jams A, the chain slips (clutch spins, sparks, grind) and B moves alone; B fully down → panel peels (1.6 s) and `child` cue; ledges deploy when a blind is > 0.75 down | ledges A (236.4–237.6, 1.1) B (237.8–239.0, 1.6) L293 |
| `dl14a.blinds` | L6083–6097, L6219–6230 | same drive (W1, W2); the heavy laundry bag on W1's cord hook holds W1 down so W2 goes alone; the light gown rides up with W1 (wrong first try) | hook 2.0 → 0.75 high L5893, roller 3.21, hem down 1.93 L5890 |

**Unity:** Core `PairedBlindDrive { A, B, jam(A), slip }` — the "Paired outputs" permanent rule.

#### 4.13h Routes, carriers and belts

**DL-06/07 return line** (L2452–2995). Carriers spawn at the hatch (63.5) every `SPAWN_EVERY` 6 s while the belt runs
and nothing is in the first 1.4 m; rise 0.6 m/s to the dock (64.0), wait 3.4 s, move at `BELT_SPEED` 0.6 m/s keeping
`CARRIER_GAP` 0.8; at the junction (67.6) take `game.route` (`chute` → tip 68° at 69.5, payload slides down the chute
into the heap, then back 0.5 m/s to the return lift at 68.9 and sink; `exit` → up the ramp blade to (71.5, 1.6), the
landing 72.7, return 74.3 and sink). Ridden exit carriers stop at the landing (`unload`), loaded ones tip the weight
toward the gallery gate's bucket (62°, 0.6 s). Riding to the chute tips him onto the heap (respawn). Levers: stop
(62.5) toggles the belt; points (63.3) only move while the belt is stopped. The route board and floor arrows show the
route (L2526–2550, L2819–2843). Points to `exit` + proud quirk.

| Constant | Value | Line |
|---|---|---|
| Path points | `COMMON` (63.5,−0.75)(63.5,0)(64.0,0)(67.6,0); `chute` +(69.5,0); `exit` +(68.25,0.32)(71.5,1.6)(72.7,1.6)(74.3,1.6) | L2471–2472 |
| `CARRIER_FLOOR` | 0.14 | L2461 |
| Payload | 0 parcels with p 0.2, else 1–3 | L2668 |
| Heap height field | centre (74.5, z −3.0), σ (4.2, 3.0), peak −0.4, floor −6.0 | L2462, L2467 |
| Heap instances | 1700 parcels + 600 letters (2 instanced draws) | L2576–2577 |
| Chute fall | accel 3.5, bounce ×−0.25 if vy < −1.2; ≤ 40 falling parcels kept | L2753–2771 |
| Lost weight returns | 4 s | L5004 |
| Scan timeline (s) | SWEEP 0.5, ANSWER 2.2, READ 2.8, REJECT 3.2 (`dead` cue), HATCH 3.6, REVEAL 4.0, CHECK 17.2 | L2465 |

**DL-08 returns belt** (L3128–3169, L3220–3229): after the pawl is set and he is 0.6 past the shaft, warning bells at
0, 0.9, 1.8 s, klaxon at 2.7 s, then crates (55% small 0.18 h, 30% 0.23, 15% tall 0.42) slide down the chute (0.75 s)
and ride the belt toward him at 0.32 m/s; he is carried back while on it; crates leave through the turn flaps (1.3 s).
Spawn every 2.9–4.2 s, only if 0.75 m clear of the chute and 1.25 m behind the last. `BELT4` 90.7–97.6 (L3015).

**Unity:** Core `CarrierLine` (polyline routes, `Junction` reading a `PointsLever`, dock, tip events) and `ReturnsBelt`;
both use `SimRng` (the prototype uses `Math.random` for crates, L3130, and a clock-seeded LCG for payloads, L2666).

#### 4.13i Water, floods and floats

| ID | Lines | Rule | Constants |
|---|---|---|---|
| `dl11.dip` (flood) | L3902, L4139, L4860–4862 | water at x 149.1–150.6, floor −0.25; he won't step in (`WaterFlinch`, spark); the duct bridges it at 0.01 | `DIP9` L3902 |
| `dl17.rig` | L5906, L6193–6259 | valve opens a 6 s run if the tank is full and ≥ 1 sluice open; the tank is shared by open sluices (rate 1/6 ÷ n × 1.06); sluice A→bed 3, B→bed 1, C→bed 2; beds drain over 20 s; tank refills over 10 s after a run; bed 1 ≥ 0.95 lifts the float latch | `valveX 336.55`, sluices 337.45/338.1/338.8, `feeds [2,0,1]`, `run 6`, `refill 10`, `drain 20` L5906 |

**Unity:** Core `SluiceRig`, `Tank`, `Bed`, `Float` — the "Water" permanent rule (weight-of-water to come).

#### 4.13j Bridges made by tipping

`dl01.cart` (L4756–4766; 0.55 h, settles at 7.27 in the trench, floor −0.8 + 0.55) and `dl11.duct` (L4854–4859; settles
at 149.85, top at 0.01; the splash is noise 1.5 to the White unless the bell holds it). DL-01's trench (6.6–8.0, −0.8)
without the cart: `trenchStuck` flinch, respawn after 2.0 s (L4764–4766, L4519–4523).

#### 4.13k Cycle clocks

| ID | Lines | Cycle | Line |
|---|---|---|---|
| `dl02.press` | L7308–7316, L7343–7352 | 2.6 s: rest 0.98; lamp blinks 0–0.5 s; down by 0.62 s to 0.055; up 0.97–1.57 s; lethal when face < 0.74 and he is under (13.62–14.28, y < 0.3) | `PRESS2` L7309 |
| `dl09.arcs` | L7321–7325, L7386–7415 | 2.4 s: arc 1 tell 0–0.3, live 0.3–0.75; arc 2 tell 1.2–1.5, live 1.5–1.95; x 105.04–105.44 / 105.77–106.17 at deck height; first touch knocks back, later touches kill | `ARCS8`, `ARC_PERIOD` |
| `dl13.lesson` | L5409–5436 | 12 s while a pupil sits in the front seat (219.4): steps out at 1.0/2.6/4.2, fold at 5.6/6.2/6.8 (0.35 s each); tree grows 6.8–10.4; brake freezes it; steps are solid only when out | `ATT.cycle` L291 |
| `dl14a.nightLight` | L5931–5932, L6221–6228 | 10 s: bright 0–3, dimming 3–4.5, dark 4.5–8, brightening 8–10; room DARK = sun < 0.05 and both blinds down; door opens after 1.2 s dark | `ATT3.cycle` L5896 |

**Unity:** Core `CycleClock { period, phase, braked }` + per-use readers. All hazard timing reads the Core clock (not
wall clock), so replays are exact.

#### 4.13l Mechanism framework summary (U-10)

`IMechanism { Id; Reset(CheckpointDef); Step(in StepContext); Snapshot(ISaveWriter); }`. Mechanisms read inputs
through typed signals (`ILoad`, `IPositionSource`, `IEngageable`) wired in the scene definition, not by direct field
access as in the prototype. Runtime `MechanismView`s read `Snapshot`-style public state each frame. Every rule table
above becomes an xUnit test (e.g. "drum alone reads OVER", "one weight lifts the gallery gate 0.38", "cage bites only
inside [1.54, 2.05]").

### 4.14 Hazards, death and respawn

**Lines:** L7305–7416 (press, gallery collapse, sump, plates on the counterweight, arcs), L7419–7454 (`DEATH`, `die`,
`updateDeath`), L7456–7493 (sparks), L2996–3000 (`respawn`), L8494 (respawn on clock).

| Constant | Value | Line |
|---|---|---|
| Death holds | crush 0.7 s (26 sparks), shock 1.0 (44), grabbed 1.15 (18), fall 0.9 (20) | L7421–7424 |
| Death cut | hard cut to black, respawn 0.6 s later; eye stutter 0.45 s | L7447–7453 |
| Non-death respawn | fade, 1.3 s on the game clock | L2997–2999 |
| Gallery collapse (DL-07) | trigger x 80.35; sags −3° over 78.95–80.05; swings −62° in 0.45 s then falls; gone at 1.6 s | L7318, L7353–7369 |
| Shaft sump (DL-08) | x 85.9–88.2 below y −0.2 → death `grabbed` (sink 0.8 m/s) | L7373–7375 |
| Persist across respawn | both plates in the tray (`persist.cw`), first cable knock-back, the White's warning, cage danger flag | L7307, L4133 |
| Sparks | pool 96, life 0.6–1.0 s, gravity 0.6 g | L7457–7493 |

**Unity:** Core `DeathRules` + `RespawnRule`; Runtime `SparkPool` (ParticleSystem, 96 max), fade overlay.
Calm mode (`game.calm`) removes sparks, shake, flicker everywhere (§4.29).

### 4.15 The White (reactive being)

**Lines:** L7040–7231 (`WATERS`, `white`, `makeNoise`, `lureWhite`, `scareWhite`, `updateWhite`, `knockBack`,
ripples), L7234–7251 (`BELL9`, `JUNCTION9`, `lane9`), L7326–7330 (`heap`, `sump7`), L7270–7273 (first sighting),
L4996 (heap glimpse on the first bucket weight). **Behaviour:** hunts by sound, never leaves water. States: `away,
patrol, listen, approach, surface, slap, strike, sink, lured, flee`. Running (|vx| > 1.25) within 1.4 m of its water,
a real landing (> 0.25 m) or a splash (1.5) is a noise; it listens, swims to the noise with ripples, surfaces; if he is
on the edge within reach: `scare` water slaps him back (unhurt), `hunt` water warns once (hiss, sink) then strikes
(`DeathGrabbed`, dragged by the `JawTip` bone); `glimpse` water only rolls. A bell lures it for 12 s (nose at the
step); running within 2.2 m breaks the lure. The shorted cable makes it flee for 20 s. Its body (2.5 m × water scale)
is clamped inside the water and only turns while deep.

| Constant | Value | Line |
|---|---|---|
| `WHITE_SPEED` | glide 0.25, approach 1.25 m/s; flee 2 m/s at depth 1.2 | L7051, L7125 |
| `WHITE_DEPTH` | 0.32 below surface | L7051 |
| Hearing | noise heard if within water x-range ± 2.5·loud | L7099 |
| Run noise | within 1.4 m of water, speed > (WALK+RUN)/2, cooldown 0.35 s | L7119–7120 |
| Listen | 0.3 s (glimpse) / 0.7 s | L7141 |
| Surface timeout | 1.6 s (glimpse) / 2.2 s | L7154 |
| Slap hit / strike hit | 0.35 s / 0.56 s (jaws close at frame 14); give up 1.3 / 2.4 s | L7157, L7161, L7175 |
| Waters | `heap` 69.62–71.93 y −0.75 glimpse scale 0.5; `sump7` 85.8–88.3 y −0.15 scare scale 0.55 reach 1.7; `lane9` 145.95–150.6 y −0.1 hunt scale 0.8 reach 1.35 ledge 0.1 | L7327–7329, L7238–7239 |
| Bell / junction | bell x 145.72, nose 146.4, ring 12 s; junction 148.92, flee 20 s, short 3.5 s | L7237, L7240–7251 |
| Ripples | pool 25, ≥ 0.18 s apart, 1.4 s life | L7206–7231 |
| Clips | WhiteGlide, Swim, Listen, Surface, Sink, Roll, Slap, Lunge, Drag, Nose (tracks shifted −1/24 s) | L7058–7062 |

**Unity:** Core `WhiteBrain` (state machine, noise queue, lure/flee timers; `NoiseEvent` emitted by motor, splashes,
bells) and `WaterBody` data from `MECH_Water_*` empties. Runtime `WhiteView` (Animator, crossfade 0.3 s, JawTip follow),
`RipplePool`. The same `NoiseEvent` bus will serve the attendant's movement zones later.

### 4.16 The escort trolley (DL-14b)

**Lines:** L5897–5900, L6352–6434, L6111–6135. **Behaviour:** patrols its rail 265.0 ↔ 274.9 at 1.1 m/s, pausing
1.2 s and turning at each end; its beam covers 2.6 m starting 0.35 ahead. Seeing him (not hidden, y < 1.25): bells, the
`att_trolley` voice, he drops what he holds and is walked back to the dormitory door (263.45) at 0.8 m/s, then it stops
2 s. Seeing the nudged figure first (nearer wins): it escorts the figure to 262.2 and stops there 6 s — the window to
pass. Hidden = in niche A (263.6–264.5) or the emptied bay (269.4–270.4) at z < −0.4.
**Unity:** Core `EscortTrolley` (generic `RailPatrol` + `ConeSensor` + `EscortBehaviour`), the template for the
attendant (full_game_plan §5 "Reactive beings").

### 4.17 Camera rig and framing volumes

**Lines:** L7644–7806 (`cam`, `captureChest`, `widthFit`, `VOL`, `frameFor`, `updateCamera`), L6470–6489 (`frameAtt`),
L5855–5879 (`frameAtt2`). **Behaviour:** one continuous side-on camera. `frameFor(x)` returns a target centre `cx`, a
volume `[distance, camera height, look height]` and a fog density, by blending per-stretch volumes with smoothstep
weights keyed on x (and on `y`, `game.upper`, puzzle state). `fit(vol, width)` widens the distance so `width` metres fit
the 35 mm frame (`hfov = 2·atan(18/focal)`, L7658–7666). The rig follows with exponential lag; acts push in.

| Rig constant | Value | Line |
|---|---|---|
| Lead | `facing·(0.6 + 0.35·\|vx\|)`; 0 while holding, in transit or exiting | L7668 |
| Follow rates | dist/height/look `dt·1.4`; x `dt·1.6`, `dt·0.6` while pace is slow or over the pit | L7793–7804 |
| Push-in | mantle 1.0, acts 0.8, realise 0.55, transit stage 0 0.4; dist × (1 − 0.22·push), height −0.25·push, look −0.2·push | L7789–7796 |
| Height follow | `+0.6·max(0, y − 0.2)`; look `+0.5·max(0, y − 0.2)` | L7795–7796 |
| Opening | from the chest (1.05 m at 45°) drifting to 0.95 m over 120 f, pull-back f120–300 to (1.9, 1.0, ≥5.2) with a 0.35 m arc, focal 50 → 35 | L7649–7657, L7777–7786 |
| Ending fog | density → 0.012 over 2.5 s while he looks up the well | L7799–7802 |

| Stretch (x, world) | Volume `[d, camY, lookY]` / fit width | cx clamp | Fog | Line |
|---|---|---|---|---|
| DL-01 alcove → hall (6.9) → bulkhead (8.9) | alcove [5.2,1.0,0.8], hall [9.2,2.35,1.95], bulk [6.0,1.15,0.9] | [1.2, 10.6] | 0.075 − 0.032·inHall | L7663, L7670–7672 |
| DL-02 Sorting Hall | [6.6,1.55,0.95] / 8.4 | [15.2, 20.9] | 0.05 | L7676–7677, L7701 |
| DL-03 weighing room | room [5.9,1.2,0.85] / 6.2 | 28.0–28.35 | 0.06 | L7679–7680 |
| DL-04 racks (from 30.3) | racks [7.4,1.6,1.1] / 6.4 | [32.0, 37.4] | 0.045 | L7681–7683 |
| DL-04 reveal pan (0–12.5 s after reveal) | reveal [10.8,2.7,1.45] / 9.5 | → 33.7 | 0.03 | L7685–7686 |
| DL-04 among the couriers | [6.2,0.95,0.72] / 6.0 | x + 0.4 in [32.2, 37.0] | — | L7688–7689 |
| DL-04 bay (from 38.4) | [6.2,1.15,0.8] / 7.0 | [41.6, 44.9] | 0.05 | L7691–7692 |
| DL-05 shrine → counter (51.6) | [6.4,1.25,0.8] / 6.8 | [49.6, 51.6] → [53.8, 57.2] | 0.045 | L7694–7700 |
| DL-06 corridor → floor (62.6) → gallery (by y) | [5.4,1.15,0.85]/5.0 → [6.6,1.35,0.85]/6.6 → [7.0,1.4,0.9]/7.0 | [60.6,62.6] → [64.8,67.2] → [73.2,78.4] | 0.05 − 0.012·upper | L7704–7711 |
| DL-07 loaded carrier / gate rising (`watchLoad`) | [10.6,2.5,1.45] / max(10.8, 2\|x − wc\| + 3.2), wc = lerp(71.4, x, 0.35) | → wc | — | L7713–7720 |
| DL-06 pit after the refusal | [11.5,2.5,−0.7] / 12.2 | → 70.9 | 0.028 | L7723–7725 |
| DL-08 goods hall / belt (88.6) | [9.4,1.75,0.65]/9.6 → [7.4,1.55,0.95]/7.8 | [84.3,87.4] → [90.6,94.8] | 0.05 | L7731–7736 |
| DL-09 cage (from 98.0) | [7.8,1.6,1.1] / 7.4 | [100.2, 103.4] | — | L7740–7741 |
| DL-09 tunnel (106.2) / vista (111.4) | [5.8,1.3,0.9]/5.6 → [7.6,2.4,1.5]/7.2 | [107.6,110.8] → [113.2,116.0] | +0.012·tunnel − 0.0575·vista | L7733–7738, L7752 |
| DL-10 lobby → shaft ride | [8.6,3.0,2.5]/8.6 → [6.4,1.3,0.75]/6.2 by `1 − y/DECK` | [122.2,125.6] → 128.2 | — | L7744–7750 |
| DL-11 ledge / lane (133.6) / hall (157.2) / rooms / bedroom / exit (168.3) | [7.6,1.5,0.75]/8.0 → [5.6,2.15,0.4]/6.0 → [4.9,1.05,0.72]/4.9 → [5.6,1.1,0.75]/5.6 | [131.4,133.4] → [136.0,155.6] → [158.4,159.3] → [161.0,162.6] → [165.2,166.6] → [169.1,170.3] | 0.0045 + 0.0615·lane − 0.025·home | L7755–7771 |
| DL-12 bin/bench → corridor (209.6) | [6.4,1.45,0.9]/8.8 → [5.8,1.35,0.85]/6.4 | [203.6,207.0] → [211.0,214.5] | 0.035 | L6473–6475 |
| DL-13 seat → lesson wide (`k13`) → gallery | [6.6,1.6,1.0]/7.6 → [7.4,2.0,1.35]/11.0 → [6.0,2.6,2.2]/6.4 | [218.9,219.8] → [223.4,224.6] → [229.0,231.2] | 0.03 | L6479–6484 |
| DL-14 | [7.0,1.7,1.25] / 10.0 | [237.6, 239.0] | 0.03 | L6486–6487 |
| Duct | [7.0,2.4,1.6] / 9.0 | x | 0.03 | L5857 |
| DL-14a / DL-14b | [7.6,2.1,1.5]/11.2 ; [7.6,1.9,1.3]/13.0 | [252.2,259.4] ; [268.2,273.4] | — | L5860–5863 |
| DL-15 balcony ↔ room (`k15` by y) | [6.2,2.5,2.0]/7.2 ↔ [7.0,1.7,1.2]/9.6 | [280.2,281.3] ↔ [284.4,289.0] | — | L5864–5869 |
| DL-16 / DL-16a | [7.2,1.8,1.2]/10.0 ; [7.8,2.5,1.7]/11.5 | [297.4,305.0] ; [314.6,319.4] | — | L5870–5874 |
| DL-17 | (volume line commented out, §9) | [328.2, 336.8 + 2.2·door] | — | L5875–5877 |

**Unity (U-13):** Core `FramingTrack` = the table above as data (`FramingZone { x0, blendIn, volume, fitWidth, cxMin,
cxMax, leadK, fog, condition }`), evaluated exactly as `frameFor`. Runtime: one Cinemachine 3 `CinemachineCamera`
("Lane") with a custom `CinemachineExtension` that sets position/aim from `FramingTrack` + the follow lag above (no
Cinemachine damping on top, to keep parity), lens focal length via `filmGauge 36` equivalent (Physical camera, sensor
36 × 20.25 mm). Fog density set from the same evaluation. Authored framing zones live in the scene definition, authored
in Blender as `CAM_` empties with custom properties (§6).

### 4.18 Authored shots, directed moments and the cue clock

**Lines:** L945–964 (`MOMENTS`, `startMoment`, `momentShot`, `momentFree`, `voicesHeld`, `keyShot`), L3687–3836
(`REALISE_KEYS`, `currentShot`, `shake`, `applyShots`), L905–927 (`Music.moment`, `momentTime`), L4610–4621
(`RINGC_LIGHT`). Design: `docs/directed_moments.md`.

| Moment | Trigger (line) | lock / release / control (s) | Peak (design / measured) | Shot |
|---|---|---|---|---|
| `kin` (DL-04, grief) | first `realise` past the gate (L1956–1958) | 19 / 21 / 22.5 (L948) | 15 / 14.85 | `REALISE_KEYS` (L3689–3692): t0–3.7 over-shoulder f30, 5.3–9 close f50, 15–21 wide f22 |
| `refuge` (DL-09, wonder) | x > `AWE_X` 113.3 (L3431–3433) | 14 / 16 / 18.5 | 10 / 9.86 | `vista`: shoulder → (X+3.2, Y+7.9, 8.5), k = smooth((t−2)/8), focal 32 → 24, look (137,12,−160) → (134,22,−150) (L3787–3793) |
| `ringc` (DL-10, grief/horror) | UP on the counterweight with the case loaded (L4584–4588) | 16 / 20 / 22 | 12 (light full) / 9.13 onto lane | `car10` → `ringc10`, k = smooth((t−6)/3) (L3714–3721); cold light ramps 9.5 → 12, off 20 (L4610, L4618–4621) |
| `window` (end, intrigue) | landing look phase at x 173.2 (L2105) | 99 / 13.6 / 99 | 6.5 / 6.39 | `ending`: rise smooth((t−1.5)/5), back after 11.5, focal 28 → 38 (L3744–3752); label at 13.6 (L2113) |

`momentShot` holds while `t < release` and not cut; after `lock`, any input sets `momentCut` (L953–957); voices and
tannoys and distant clanks are suppressed while a shot holds (L958, L6685, L7964). `applyShots` (L3811–3836) blends a
shot in at rate 1.4 and out at 0.8 (smoothstepped weight), follows the shot at `dt·ease·1.6`, and **for moment shots
uses the cue-clock delta (≤ 0.5 s) as dt** so a frame stall cannot leave the camera behind the music. Shake: amplitude
`a` → x 0.035a·sin(1.7s), y 0.03a·sin(2.3s+1), look-y 0.02a, decay `e^(−5t)`; calm mode disables it (L3810).

Non-moment authored shots (all from `currentShot`, L3698–3809):

| Shot | Condition | Pose (three.js coords) | Focal / ease | Line |
|---|---|---|---|---|
| `label` | `CheckLabel` quirk, clip f > 2 | label centre + 0.27 forward + (0, 0.15, 0.05) | 50 / 3.0 (wake) or 1.1 | L3735–3742 |
| `scan` | scanner phase `scan` | (60.65, 0.64, 2.9 − 0.3·smooth(t/4)) → (62.3, 0.95, −0.3) | 38 / 1.6 | L3797 |
| `pit` | phase `reveal` | (X−1.4, 1.2, 2.0) → (69.4, 4.6, 9.6); k = smooth((t − 5.2)/6.5) | 32 → 26 / 0.9 | L3799–3803 |
| `check` | phase `check` | (min(X+0.6, 69.2), 0.78, 1.3) → (X+0.02, 0.52, 0) | 50 / 1.2 | L3806 |
| `hopscotch` (long) | `HopscotchLong` | crane keyed on clip time 3.0–6.2 up, 7.6–10.0 down | 40 → 32 → 40 / 1.0 | L3773–3779 |
| `viewer` | `LookViewer` f64–150 | (X+0.1, Y+1.1, 0.25) → atrium, yaw ±0.55 at 0.32 rad/s by input | 110 / 4 | L3764–3770, L6736–6747 |
| `marks` | 6.0 s after the desk clears (cancellable after 3.0) | (167.55, 0.72, 0.9) → (167.55, 0.68, −1.0) | 50 / 1.2 | L3468, L3553, L3755 |
| `knock` | knock act (first time) | (156.5, 0.72, 1.72) → (157.42, 0.64, 0.12) | 28 / 1.2 | L3757 |
| `terminal`, `toy` | present / toy acts | (X+0.55, Y+1.05, 0.75) → (167.6, 0.9, −1.0); (X+1.15, Y+1.15, −0.1) → (165.08, 0.44, −0.36) | 42 / 1.4; 34 / 1.6 | L3758–3759 |
| `secret` | in a secret room | `SECRETS[i].cam/look` | 24 / 1.3 | L3730–3732 |
| `sit15` | sat in Mara's chair > 0.5 s | (285.15, 0.62, 1.45) → (288.6, 0.72, −0.9) | 28 / 0.9 | L3723 |
| `drawer17` | reading the drawer | (330.62 − 0.69k, 0.92 − 0.17k, −0.06 + 0.01k); k over 3.0–4.2 s | 24 → 35 / 1.2 | L3725–3728 |

**Unity (U-13):** Core `CueClock` (moment name, start, time, frozen while paused/hidden, fallback to sim time after
0.6 s unstarted / 2.0 s stalled, L918–919), `MomentTimeline` (lock/release/control), `ShotSelector` (the rules above
→ a `ShotPose`). Runtime `MomentPlayer`: one Timeline asset per moment (`Moment_kin`, `Moment_refuge`,
`Moment_ringc`, `Moment_window`) with Cinemachine and light tracks, `PlayableDirector.timeUpdateMode = Manual`,
`director.time = CueClock.Time` each frame (keyframes copied from `docs/directed_moments.md` and the lines above);
procedural shots (label, pit…) are a `ShotCamera` posed by `ShotSelector` every frame, blended by Cinemachine with a
custom blend curve reproducing the 1.4/0.8 smoothstep weight. Moment `dt` coupling: the camera reads the cue clock, not
`Time.deltaTime`.

### 4.19 Character polish, hints, glints, weight lamps, gauges, quirks

**Lines:** L7495–7560 (`HINTS`, 50 rules), L7561–7575 (`headLook`, `hintTarget`), L7578–7642 (`updateCharacter`),
L3838–3873 (quirks, `PEEK_SPOTS`), L6932–7030 (`Glints`), L6848–6892 (`Pips`), L6893–6931 (gauge face),
L6346–6349 (chapter 1 stall rule). **Behaviour:** idle 5 s near the next useful thing → head turns to it; 10 s → body
leans; 18 s with the assist option → key glyph. Head look is limited like a neck and drops targets behind him. Scripted
looks (`game.lookAt`: heap, platform, window, wheelA, tray, door17, bench12, crank14a, drawer17, rig17) and early-curio
glances (1.8 m, once, ≤ 2.2 s each). Glints: every 0.25 s sweep ±3 m in 0.1 m steps asking the resolver; each answer
gets a sprite at the thing's real anchor (≈60 anchor rules, L6943–6966, L6436–6448), the current Use target is
brightest and carries the E; the two nearest get real lamps from the pool. Pips: brass lamp plates (DL-07 bucket 2,
DL-09 tray 2, DL-10 car 1). Chapter 1 hints wait for a failed attempt and 20 s without progress.

| Constant | Value | Line |
|---|---|---|
| `HINT_LOOK` / `HINT_LEAN` / `HINT_GLYPH` | 5 / 10 / 18 s idle | L314 |
| Head limits | yaw ±70°, pitch ±35°; drop if > 110° or > 6 m | L7561, L7566 |
| Head/body weights | head 0.85·w, body 0.15·w; w rate `dt·2.5` | L7616, L7624–7625 |
| Peek | idle ≥ 2.5 s at 4 edges (trench, cart edge, pit rail, shaft) | L3858–3872 |
| Glints | 10 sprites, scale 0.16 + 0.12w, opacity 0.55w; 2 lamps 0xffc896 1.7 m, 1.3 (current) / 0.75 | L6938, L6980, L7013–7026 |
| Pips | lamp r 0.023, 0.07 apart; amber 0.15 → 3.2 lit, green when full, red flash 1.4 s | L6851–6891 |
| Pip plates | `bucket6` (72.0, 1.78, −1.05); `tray9` (100.3, 4.68, −0.42); `car10` (124.07, 2.31, −0.29) | L6887–6889 |
| Stall hint | 20 s after `failAtt` with no `progressAtt` | L6349 |

**Unity (U-11, U-17):** Core `HintRules` (data: region, predicate id, anchor, key), `HeadLookLimits`, `GlintSweep`
(uses `InteractionResolver`), `Pips`. Runtime `HeadLookRig` (bone post-process after the Animator, `LateUpdate`),
`KeyCap` UI. Port the 50 `HINTS` predicates as named C# predicates per scene (they read mechanism state).

### 4.20 Lights: static lights, region lights, light zones, the light pool

**Lines:** L1457–1478 (`buildLights`), L1550–1578 (`applyLights`, opening flicker), L2209–2221, L2608–2617,
L3068–3092, L3484–3492, L4052–4087, L5174–5222, L7872–7885 (scene lights), L2622–2657 (`lightZoneFor`,
`setRegionLights`), L8536–8598 (`LIGHT_POOL`, `buildLightPool`, `updateLightPool`). **Behaviour:** every light is
created in code (the GLBs contain no lights). At pool build every light becomes a **proxy** on layer 31; each frame the
lit proxies nearest the camera are copied into a fixed pool, so the shader light count never changes. Region lists
switch proxies on with the region; two sub-region zones (Ration Hall, Up Only) swap lists inside a region.

| Constant | Value | Line |
|---|---|---|
| `LIGHT_POOL` | point 10, spot 4, spotShadow 2, dir 2, hemi 2 | L8542 |
| Proxy layer | 31 | L8542 |
| Score | `intensity·(distance or 10) / (1 + gap² + 0.05·dx²)`; `kick` +1e6, glint lamps +1e5; skipped if > 9 m beyond reach | L8572–8574 |
| Shadow overflow | shadowed spots beyond 2 light without shadow; empty shadow slot stops updating | L8577–8583 |
| Shadow maps | 512² (work lamp 1024²); relay lamp casts only off touch devices | L1467, L1472, L2212 |
| Hemisphere (r1) | 0x26332f / 0x0b0b0a, 0.45 | L1461 |
| Rim (r1) | dir 0x8db4c8 0.35 from (5, 3, −8) | L1462 |
| Kick (character) light | point 0xffe2c4, 2.6 m, 0.55, at (x + 0.5, y + 1.0, 1.3) | L1475, L1573, L7587 |
| Opening flicker | parcel lamp f18–40; work bulb f226 pattern; eyes f225 | L1553–1577 |
| Zone `ration` | from x 47.4 (47.9 − 0.5; hysteresis 1.0) | L2627 |
| Zone `uo` | from x 117.8 (118.8 − 1.0; hysteresis 1.4) | L2628 |
| Region light switches | transit stage 1 → r2 (L2149); scan → r3 (L2781); cam.x > 87 → r4, < 86 → r3 (L3237–3238); x > 133.6 → r5, < 133.2 → r4 (L3560–3561) | — |
| Lit proxies at once (static read) | DL-01 ≈ 14, DL-02–04 ≈ 23, Ration Hall ≈ 17, DL-06/07 ≈ 17, DL-08/09 ≈ 20, Up Only ≈ 30, DL-11 ≈ 28; chapter 1 ≈ 68 (all of region 6); ≈ 95 + 68 proxies in all | §8 |

**Unity (U-15):** lights move to Blender as `LGT_` empties (type, colour, intensity, range, angle, penumbra, decay,
shadow, zone, flicker id) so the art source of truth includes them (the prototype's per-light values in the lines
above are the import seed; `LightBuilder` creates `LightProxy` components). Runtime `LightPool` owns per-tier real
lights (§8) and copies top-scoring proxies with the same score. Zones: `LightZoneSwitch` from Core region/zone state.
Flicker/pulse drivers (`applyLights`, ration strip, Up Only pendant, lane bulb) are Core `LightCurve`s keyed by id;
calm mode substitutes the steady curves (L1530, L1543, L4928, L4663, L3564).

### 4.21 Emissives and in-world displays

**Lines:** `EMIT` L469–490, `glow()` L3535 (24 call sites) and 34 direct `emissive[...]` writes, canvas panels L2485–2550 (scanner screen 256×192,
route board 312×180), L3495–3533 (terminal 256×192, `stampLabel`), L6893–6931 (balance gauge face 512²), scrolling
belt textures (L2556–2561: `BELT_SPEED·6` u/s; L3055–3061: `BELT4.speed·2`), DL-14 chain map (0.6 v/s, L5448).
**Unity:** `EmissiveDriver` sets emission intensity per named emissive group by `MaterialPropertyBlock`.
Displays have finite states → pre-render state sprites in Blender/Editor (scanner: idle/scan/read/reject;
terminal: idle/read/nobody/forward; route board: 2 routes × belt state); the label stamp becomes two pre-authored decal
overlays (`FWD SCHOOL RING B`, `FWD WORKS RING A`). Move the gauge face drawing into `art/` so Blender owns it.

### 4.22 Atmosphere and particles

**Lines:** L1480–1522 (dust 1,000 points following the camera ±14 m; grit 34 pieces at opening frames 348–364),
L7808–7966 (hooks, drips, steam 34 wisps with puffs every 2.5–6.5 s, 3 light-shaft cones at opacity 0.05 ± 0.02,
searchlight sweep `t·0.12` intensity 140, cable crackle every 3–8 s, cord lamp, door glow, distant clanks every
6–14 s), L3088–3092 (atrium sky shafts), L7456–7493 (sparks), L7203–7231 (ripples), L4028–4043 (body sheet ripple
vertex wave), L5171 (trolley beam cone, additive 0.08, no fog). **Unity:** ParticleSystem (CPU, Switch-safe) for
dust, steam, sparks, drips; additive unlit shader for shafts and cones (fog off); the body ripple is a vertex
displacement in a Shader Graph variant driven by `_RippleAmp/_RippleTime`.

### 4.23 Audio: sound effects

**Lines:** L556–774 (`Sound`). **Behaviour:** every effect is synthesized in WebAudio (oscillators, noise bursts,
biquads) into a master (0.8) with a 2.4 s exponential-decay convolution reverb at wet 0.32 (L570–575). About 60
one-shots (`tick relay spark answer servo click grit chirp worried tap rattle step jump land lampClick buzzShort
ratchet doorRumble doorOpen strain drip crackle groan scrape bonk creak clank chain thud distant plate gateTick
gateSlam lift setDown squeak rowOn knock scanSweep reject hatchLift bell klaxon beltStop clunk clack tumble pawlClick
pawlClatter liftCrash lurch alarmBell crateLand found curio(scale|stamp|mug|mugDown|sit|wind|coin|radio|switch|paper)
radio splash zap death(crush|shock|grabbed|fall)`) and 9 continuous loops with a level parameter (`hum buzz hiss roll
tubes belt drum air drag`). Footsteps fire on the walk-cycle half phase (L2069–2075).
**Unity (U-16):** `SfxBaker` (Editor + a headless Chromium script reusing these exact functions through
`OfflineAudioContext`) renders 4 random variations per one-shot and seamless loops to WAV; `SfxBank` ScriptableObject
maps the prototype names to clips; loops become looping `AudioSource`s whose volume follows the same level parameters.
One AudioMixer: `Master > {Music (limiter), SFX (reverb send), Voice, Ambience}`. This keeps parity now and lets a
sound designer replace clips later without code changes.

### 4.24 Music, cues and ambience

**Lines:** L776–944 (`Music`), L8145–8168 (`sceneAmbience`, `updateAmbience`). **Behaviour:** two layers: one **cue**
at a time and one **ambience** loop that crossfades between four prologue loops (chapter 1 uses the old 48 s bed).
A cue hides the ambience (fade 1.5 s, or 4/2 s by its intro bars); at the cue's handover bar the scene loop restarts
under its tail. Moments start at full level 0.1 s ahead on the audio clock (§4.18). A limiter sits on the music bus.

| Constant | Value | Line |
|---|---|---|
| Files used (`FILES`) | 12 `prologue_cue_*`, 4 `prologue_loop_*`, `dl01_bed`, `dl05_child`, `dl01_end` | L783–787 |
| Levels | cues 0.9 (child, endAtt 0.6); loops 0.9; bed 0.26 | L788, L802–803 |
| Loop region | loops [2, 34] s (files padded 2 s); bed [2, 50] | L799–803 |
| `HAND` handovers (s, intro bars) | wake 48/0, hall 32/1, threshold 24/1, racks 36/1, kin 28/0, dead 40/0, latch 8/0, refuge 24/0, ringc 24/0, childP 36/0, window 20/0, end 60/0 | L792–793 |
| Fades | cue fade-in 1.2 s; stop 1.5 s; moment 1 s; ambience crossfade 4 s; bed 6 in / 3 out; failure → other 2 s | L861, L886, L807, L930, L8166 |
| Limiter | threshold −24 dB, knee 12, ratio 4, attack 0.25 s, release 1.2 s | L823–824 |
| Pause / duck | music × 0.45 paused; × 0.4 under a voice (in 0.4 s, out 1.5 s) | L818, L941 |
| `PRIME` | 0 (decoder priming) | L797 |

Cue triggers: `wake` opening (L8068); `hall` first x > 7.3 (L2066); `threshold` door open (L1890); `racks` through the
DL-03 gate (L2403); `kin` (L1958); `dead` scanner reject (L2801); `latch` pawl (L3125); `refuge` (L3433); `ringc`
(L4588); `childP` marks (L3547); `window` (L2105); `end`/`endAtt` on finish (L8186–8189); chapter 1: `bed` (L8092),
`child` at DL-14's peel (L5474) and DL-15's dismissal (L5734); music stops for the rack's hush (L5760) and returns at
x 311 (L5765). Ambience map (L8147–8161): DL-01 `lower_works`; DL-02/03 `lower_works`, racks `heaps`, Ration Hall
`order`; DL-06 corridor `order`, floor `lower_works`; DL-08 `lower_works`; DL-09 cage danger `failure` (fade-in 1 s)
until caught, then silence through the tunnel; after the city `order`; Up Only `order`, riding down `heaps` × 0.6;
DL-11 `heaps` × 0.6, the bedroom silent. Unused music files in `assets/music/`: `dl01_dead, dl01_hall, dl01_kin,
dl01_racks, dl01_threshold, dl01_wake, dl04_latch, dl04_refuge, prologue_collapse, prologue_lastcar` (do not import).

**Unity (U-16, with U-13):** `MusicDirector` (Runtime) on two `AudioSource` pairs (cue A/B, ambience A/B) using
`PlayScheduled`/`SetScheduledEndTime`; trim the 2 s padding at import so loops are clip-native (Unity has no
loopStart/loopEnd on `AudioSource`); `MusicDirectorModel` in Core owns the decisions (which cue, queue, handover times,
ambience wanted) so they are replay-testable. The moment clock is `AudioSettings.dspTime − start − outputLatency`
(latency from `AudioSettings.GetDSPBufferSize` / output sample rate; Switch value to be measured).

### 4.25 Voices, tannoys and ambient emitters

**Lines:** L966–1143 (`Voice`), L6520–6575 (`VOICE_LINES` 30 ids, `VOICES` 13 placements), L6647–6692 (cards,
tannoys), L1145–1211 (`Ambience` emitters), L6577–6598 (`EMITTERS` 19). **Behaviour:** one voice at a time through a
treatment chain (waveshaper drive → high-pass → low-pass → optional ring mod → dry + room convolver + optional
"next speaker" echo), with crackle and wow/flutter; music ducks under it. **No recordings exist yet**
(`assets/voice/` is absent): every line plays the placeholder murmur (two formant band-passes on a buzz, syllables
from word counts) with subtitles. Tannoys play once as he passes; again only after leaving earshot and 150 s.
Positional falloff is linear over `reach` (default 6 cards, 9 tannoys).

| Treatment | rate / pitch | band (Hz) | drive | crackle | wow | room | extras | Line |
|---|---|---|---|---|---|---|---|---|
| tannoy | 1 / 0 | 380–3400 | 1.6 | 0.005 | 2 | 1.4 (wet 0.2) | two-note chime 659.3/523.3 Hz, echo 0.23 s | L976 |
| dispatch | 1 / 0 | 330–3600 | 1.3 | 0.003 | 0 | 1.2 (0.18) | ring 47 Hz, echo 0.23, machine | L978 |
| card | 1 / 0 | 250–3500 | 1.6 | 0.02 | 9 | 0.5 | — | L979 |
| card_worn | 0.97 / 0 | 300–3000 | 2.2 | 0.045 | 18 | 0.5 | drops | L980 |
| child | 1.06 / +4 st | 250–3800 | 1.6 | 0.02 | 9 | 0.6 | — | L981 |
| elder | 0.95 / −1.5 st | 250–3300 | 1.6 | 0.025 | 12 | 0.5 | tremble 5.2 Hz | L982 |
| machine | 1 / 0 | 600–2600 | 3 | 0.006 | 0 | 0.9 | ring 31 Hz | L983 |
| radio | 1 / 0 | 500–2800 | 3 | 0.08 | 6 | 0.2 | static swell | L984 |

Emitter kinds (L1157–1193): `buzz` (100 Hz saw, bp 1800), `hum` (50 Hz, bp 160), `lap`, `wind`, `static`, `machine`
(filtered noise with LFOs), `drip`, `tick`, `fan`, `musicbox` (event blips); gain = level·k² with k = 1 − |dx|/reach.
**Unity (U-16):** `VoicePlayer` with one AudioMixer group per treatment (Unity's Highpass, Lowpass, Distortion, Echo,
SFX Reverb, Flange for wow) and baked crackle/chime clips; `VoiceCard`/`Tannoy` placements as `MECH_Voice_*` empties;
subtitles from `VOICE_LINES` exported to a localisable string table (Unity Localization later). Placeholder murmurs
baked offline per line by `SfxBaker` so the build has audio until recordings arrive.

### 4.26 Letters and the reader

**Lines:** L3904–3973 (`LETTERS`, `SLOTS`, `letterState`, `LETTER_TEXT`, `Letters`), L4470–4490 (pick up, post),
L4770–4781, L4838–4849, L4863–4872 (each letter's fall), L4874 (slot lamps). **Behaviour:** three letters (`tube`
DL-02 at 14.6 drops from the tube cup when he passes; `heap` DL-07 on the gallery at 76.4 falls as he passes under;
`c110` DL-11 slips from C-110's slot when the duct bridges and flutters to the far kerb 151.05) and three slots
(16.0; 77.2 upper; 156.75). Picking up scans the letter: an overlay shows front/back images and text; Use (after
0.6 s), 12 s, or walking 1.6 m closes it. DL-17's two records scan themselves (L5704). State survives respawns and
checkpoint reloads; Start over clears it (L4133).
**Unity:** Core `Letters` (states `cup|rail|slot → falling → floor → held → posted:<slot>`), Runtime `LetterReader`
UI with the PNGs in `assets/letters/`.

### 4.27 Curiosities and secret rooms

**Lines:** L5099–5121 (`CURIOS`, 13 entries incl. the cot), L6693–6798 (`curioHere`, `findCurio`, `updateCurioAct`,
`curioProps`, `buildCurios`, clock), L6799–6847 (glances, light pools), L6491–6519 (`SECRETS`, 5 rooms),
L6599–6646 (`secretHere`, `updateSecretAct`). **Curios:** scale 1.45, cord 0.59, dispatch 1.0, cot 4.6 (deep, z −2.3),
franker 12.8, mug 15.2, rack 41.08 (after the courier is seated), chair 60.8, clock 73.38 (upper; ticks 75 s),
hopscotch 108.15, viewer 114.6, radio 163.0, switch 158.72. Early ones get a warm floor pool and a glance until used;
a find chimes and shows "◆ n / 13". **Secret rooms:** `reader` (DL-06, 66.52–67.22, not while a carrier passes within
1.0), `den` (DL-09, 106.86–107.48, crouch through the vent), `lostprop` (DL-12, 211.6–212.3), `cupboard` (DL-14,
234.5), `hide15` (DL-15, 279.8). He walks a path into the room, the camera frames it, the room's voice card plays after
1.4 s, any input after 2 s walks him out.
**Unity:** Core `Curiosities`/`SecretRooms` (data + state), acts as in §4.12; props animated by keyed curves
(`curioProps` keys become AnimationClips exported from `art/pass2/build_curios.py`).

### 4.28 Checkpoints, persistence and save

**Lines:** L3976–3979 (`CP_ORDER`, `past`), L7975–8014 (`CHECKPOINTS`, 37 entries), L8015–8056 (`resetWorld`),
L4091–4132 (`resetCh1`), L5228–5242, L5538–5554, L5912–5924 (chapter 1 resets), L7306–7307 (`persist`), L4133
(`clearLetters` = start over), L8083–8122 (`startPlay`, `loadCheckpoint`), L8333–8377 (`Resume`, context-lost).
**Behaviour:** a checkpoint is a name in a total order; every mechanism's state on reload is derived from
`past(checkpoint, X)` flags (e.g. the cart is a bridge if past `hall`), so loading a checkpoint rebuilds the world
deterministically. Checkpoints are set by position/state triggers in each scene (see §5). Outlive respawn: `seen`
moments, `letterState`, `curioFound`, `secretFound`, `voiceFound`, `persist {cw, shockedOnce, warned, cageDanger}`.
`Resume` stores `{cp, scene, at, found{curio,secret,voice}, read[]}` in `localStorage['dl01-resume']` whenever the
checkpoint changes; finishing the prologue saves `school`. Options persist as `dl01-<name>`; brightness `dl01-bright`.
**Unity (U-14, as built in #11):** Core `SaveModel { version, checkpoint, seenMoments, letters, curios, secrets,
voices, persistFlags, options, playTime }` plus a `mech/` mechanism snapshot, written by `SaveCodec` in a
hand-rolled binary format (DLSV: magic, u16 version, CRC-32; no reflection, so IL2CPP/AOT-safe) through `ISaveStore`
(Steam: file in `Application.persistentDataPath` + Steam Cloud; Switch: save-data mount, commit on checkpoint).
`CheckpointDef` (scene id, x, y, region flags, solved-set) as data. The prototype's rule still holds underneath: the
world is first **derived** from the checkpoint name; the stored snapshot is then applied on top, and skipped when its
scene no longer matches (or fails to read), so a stale save falls back to the derived world. Save on checkpoint change
(rate-limit to one write per 2 s on Switch).

### 4.29 Title, pause, end cards, options and accessibility

**Lines:** HTML L129–253 (title with options and scene select, pause with letters list, lost-context card, end card),
L8123–8133 (`togglePause`), L8169–8196 (`tally`, `finish`: 4 s fade, end card at 5.2 s), L8282–8331 (options),
L6461–6469 (chapter 1 end text). Options: auto-run, sound, music, prompts/glints, stuck-assist glyph, brightness
0.8–1.8, calm mode (no flicker, flashes, shake, sparks; bloom 0.35), telemetry. Touch: four on-screen buttons.
**Unity (U-17):** UI Toolkit screens; `Settings` (Core POCO) persisted via `ISaveStore`; add subtitles size/background,
rebinding, hold-to-press alternatives (DL-16's held lever), and a photosensitivity check for the relay pulse
(`DL-01_the_wake.md` §9). Calm mode must be honoured by every flicker/shake/spark source listed in §4.14, §4.20, §4.22.

### 4.30 Telemetry

**Lines:** L8198–8280. **Behaviour:** anonymous events `{i, type, t, play, scene, x, cp, ...}` batched (25 events or
15 s) to `?telemetry=` URL, kept in a rolling 8,000-event log, savable as JSON with a per-scene time summary; `perf`
every 10 s (fps, worst ms, long frames, dpr). Event types used: `session begin skipIntro use scene checkpoint idle perf
death curio secret voice letterRead weigh hatchTwitch cageDip liftBuzz weighLamp option pause reloadCheckpoint startAt
chapterStart resume contextLost end leave hidden prompt whiteWarn unjam blinds lessonStart lessonBrake peel seat15
dismissal stored16 rackFull door17 float17 duct drawer placement hook14a gownHem blinds14a nightBrake figOut14b hide14b
caught14b figSeen14b figKept14b call16a dumbwaiter load16a rode16a sluice17 valve17 dark14a continue loadFail`.
**Unity:** Core `EventLog` (same schema, so `tools/telemetry/summarise.py` keeps working); Runtime uploader on PC
builds only (opt-in), disabled on Switch retail.

### 4.31 Test hooks and the simulated player

**Lines:** L8530–8534 (`window.__dl01`), L8467–8478 (`window.__sim` fixed 60 Hz stepping), L1784–1802 (`auditNear`).
`tools/sim/bot.js` (808 lines) drives `input` directly with coroutines (`walk`, `goTo`, `useAt`, `until`) per scene,
with a seeded player model (skill, curiosity) adding think/look/react times; `sim.mjs` runs it in headless Chromium;
`audit_near.mjs` runs the overlap audit from every checkpoint; results in `tools/sim/results_*.jsonl`.
**Unity (U-18):** a headless .NET runner over `DeadLetter.Core` only (no Unity): `ReplayHarness` steps `StepPipeline`
at 60 Hz with a scripted `IInputSource`; port `bot.js`'s scene scripts to C# `IEnumerator` coroutines against the same
Core queries (`Near()`, `Scene()`, mechanism state); outputs the same JSONL schema. Acceptance: mechanical times per
scene within ±5% of `results_*_mechanical.jsonl` (prologue 8:41 with moments, chapter 1 6:40), zero overlap-audit hits,
and PlayMode tests replaying recorded inputs in the real Unity scenes.

---

## 5. Per-scene table, DL-01 to DL-17

Mechanism IDs are the proposed `MechanismId`s (stable across saves). "Tris/prims" are measured from the set GLB by
mesh-centre x (§8), excluding D-17, the dormant couriers and the >30 m wide atrium/backdrop meshes (88,923 tris, 27
prims, loaded with DL-09–11). Checkpoints are `name x (y)` from `CHECKPOINTS` (L7975–8014) and their triggers.

| Scene | x (region) | Systems used | Assets (builder; tris/prims) | Mechanisms (IDs) | Checkpoints | Moments, shots, cues | Scene code (lines) |
|---|---|---|---|---|---|---|---|
| **DL-01 The Wake** | 0–12 (r1) | opening timeline, motor (first hop: fallen conveyor 3.6–4.4 h 0.22), latch, shutter + chain, push + tip, trench fail, crank door, relay pulse, hints, curios (scale, cord, dispatch, cot), tannoy `tan_depot_1`, passage transit | `set`: `art/dl01` + pass2 curios, pass3 lore, pass4 `build_story_depot`, pass10 cot; `d17` (37,328 / 104) | `dl01.relay`, `dl01.latch`, `dl01.shutter`, `dl01.cordLamp`, `dl01.scale`, `dl01.cart` (pushable, tips into `dl01.trench` 6.6–8.0, −0.8), `dl01.crank`, `dl01.door` | `start` 1.0; `shutter` 2.9 (latch released, L1677); `hall` 8.35 (past the trench, L2065); `door` 9.62 (door open, L1890) | opening camera (480 f), `labelWake` label shot + `dispatch_wake/item`; cues `wake`, `hall`, `threshold` | L275–303, L1460–1592, L1617–1707, L1803–1901, L2129–2157, L3885, L4756–4769, L4923, L7837–7966, L8057–8082 |
| **DL-02 The Sorting Hall** | 12–25 (r2) | franking press hazard (death `crush`), carry/place box, table (0.75) and gantry (1.35) climbs, tube letter, slot 2, curios franker/mug, voice `card_sorter`, tableaux lit | `art/sorting_hall`, pass4 sorters, pass6 tableaux (46,174 / 115) | `dl02.press`, `dl02.box`, `dl02.tubeLetter`, `dl02.slot` | `room` 13.2 (end of transit, L2143) | none (frame only) | L3887–3888, L4770–4782, L5110–5111, L7308–7316, L7343–7352, L7675–7677 |
| **DL-03 The Weight of the Job** | 25–30.6 (r2) | load plate → follower gate, carry weight, push trolley (two grips), reveal (row lights 1.0–7.0 s) | `art/dl02` + OFF2 (10,560 / 34) | `dl03.weight`, `dl03.trolley`, `dl03.plate`, `dl03.gate`, `dl03.rowLights` | `weighroom` 25.9 (x > 25.6, L4946); `solved` 29.95 (plate holds without him, L2396–2403) | reveal pan (framing), gate slam startle; cue `racks` on passing the gate | L318–329, L2159–2450, L7529–7537 |
| **DL-04 The Racks** | 30.6–47.9 (r2) | directed moment `kin`, 56 instanced dormant couriers, nudge, drag courier, bay plate + cradle + door, curio rack, tannoy `tan_racks` | `art/dl02` racks hall + `art/racks`; `couriers` (31,822 / 96 + 48 instanced) | `dl04.nudge`, `dl04.courier` (pushable ±), `dl04.bayPlate`, `dl04.cradle`, `dl04.bayDoor` | `bay` 47.1 (through the door, L4947) | `kin` (REALISE_KEYS), among-couriers frame, `bayTouch` act | L1955–1959, L2178–2207, L2291–2314, L3689–3692, L3890, L4491–4495, L4783–4822 |
| **DL-05 The Ration Hall** | 47.9–59.8 (r2, zone `ration`) | weigh-in scale, push drum (on, then past), drag body (sheet ripple), hatch crawl (gap 0.64), label check, voice `card_queue`, tannoy `tan_rations`, flickering strip light | `art/pass3/build_ration_hall.py` (69,701 / 71; shrouds 16 draw calls, README L457) | `dl05.drum`, `dl05.body`, `dl05.weighIn`, `dl05.hatch`, `dl05.servedFlag` | `ration` 48.6 (L4935); `hatch` 57.05 (past the crawl, L4936) | `label5` at 51.9–53.9; ambience `order` | L3447–3454, L4028–4043, L4072–4076, L4276–4281, L4878–4932, L4941 |
| **DL-06 Return to Sender** | 59.8–69.4 floor (r3, lower) | scanner sequence, carrier line (dock, junction, chute tip), stop + points levers, board/ride/alight, chute ride → heap → respawn, pit reveal, heap instances, displays, curio chair, secret `reader`, voice `card_heap`, White `heap` glimpse | `art/dl03` + OFF3 (DL-06+07 together 52,964 / 165; heap 2 instanced) | `dl06.scanner`, `dl06.line`, `dl06.dock`, `dl06.stopLever`, `dl06.points`, `dl06.chute`, `dl06.routeBoard` | `scanned` 63.3 (after the label check, L2814) | `scan`, `pit`, `check` shots; cue `dead`; `tan_scanner` | L2452–2995, L6497–6500, L7327 |
| **DL-07 The Heap** | same floor + gallery 71.85–80.4 (r3, upper) | carry weights → load carriers (two per tub) → bucket, gallery gate (0.38 per weight, 1.4 with two), parcel slide, heap letter, slot 6, curio clock, gallery collapse (no way back), Pips `bucket6` | `art/dl03` | `dl07.weight0`, `dl07.weight1`, `dl07.bucket`, `dl07.gate`, `dl07.slide`, `dl07.collapse` | `landing` 73.0 (alight at the gallery, L2955); `gallery` 75.3 (past the gate, L4948) | `watchLoad` wide frame; `Proud` on points | L3891–3895, L4441–4458, L4496–4510, L4823–4849, L4977–5005, L7318, L7353–7369 |
| **DL-08 The Handbrake** | 80.5–97.6 (r4) | heavy push, pan → Lift 2 platform, pawl, teeter, sump (White `scare`; falling in = death), rail climb off the trolley, returns belt with crates, fallen goods-lift set piece | `art/dl04` belt side + OFF3, pass4 `build_story_shafts` (15,822 / 114) | `dl08.trolley`, `dl08.pan`, `dl08.platform`, `dl08.pawl`, `dl08.sump`, `dl08.belt` | `goods` 81.9 (enter region 4, L2044); `latched` 89.2 (past the shaft with the pawl set, L3419) | platform look; cue `latch` | L3002–3337, L3439, L3897, L7328–7329, L7371–7376 |
| **DL-09 The Slipping Cage** | 97.6–118.8 (r4) | three climbs (2.2/2.8/3.4), plates → tray, slipping cage + pawl, cage crash death, live cable arcs (knock-back then death), hopscotch (long), secret `den`, `refuge` moment at the rail, coin viewer, label check, tannoy `tan_bridge`, atrium vista (far plane 400 m) | `art/cage`, `art/dl04` tunnel side + OFF4, pass2 plates/sump/cable, pass3 gauge/chevrons (33,026 / 164; atrium in "wide") | `dl09.plate0`, `dl09.plate1`, `dl09.tray`, `dl09.cage`, `dl09.cagePawl`, `dl09.arc1`, `dl09.arc2` | `cage` 100.8 (y 3.4; L4949); `landing8` 103.3 (y 1.6; caught, stepped off, L4950); `tunnel` 107.7 (L3421) | `refuge` moment, `hopscotch` and `viewer` shots; ambience `failure`; `label9` at 114.9–118.8 | L3017–3019, L3346–3437, L3899–3900, L5007–5096, L6502–6504, L7320–7325, L7377–7415 |
| **DL-10 Up Only** | 118.8–127.9 (r4, zone `uo`) → ride to r5 | carry case → car plate, two UP buttons (buzz when empty), service crank door, counterweight ride, `ringc` moment + cold light, Pips `car10`, voice `card_lastcar`, tannoy `tan_relocation`, lobby hidden for the city shot | `art/pass3/build_up_only.py`, pass4 `build_story_ringc` (71,940 / 157) | `dl10.case`, `dl10.carPlate`, `dl10.lift`, `dl10.upButton`, `dl10.serviceCrank`, `dl10.serviceDoor`, `dl10.serviceUp`, `dl10.counterweight` | `uponly` 119.4 (y 1.6; L4937) | `ringc` moment (`car10` → `ringc10`); ambience `order` → `heaps` × 0.6 | L3455–3461, L4526–4675, L8441–8449 |
| **DL-11 The Child at the Address** | 127.9–175 (r5) | barricade crawl (0.62), flooded lane + White `hunt` (warning, then death), doorbell lure, junction short, duct push → bridge, C-110 letter, slot 9, C-114 knock + cord door, facade fade, hall switch and radio curios, toy, desk drag, marks, terminal present → label stamp, `card_mara_parent`, ending (`window` moment, stair, fade) | `art/dl05` + OFF5, pass4 drowning (138,586 / 267) | `dl11.barricade`, `dl11.lane`, `dl11.bell`, `dl11.junction`, `dl11.duct`, `dl11.c114Door`, `dl11.facade`, `dl11.desk`, `dl11.terminal` | `ringc` 135.25 (past the barricade, L3675); `bedroom` 164.1 (L3680); `forwarded` 167.1 (L3624) | `knock`, `marks` (6 s), `terminal`, `toy`, `ending` shots; `window` moment; cues `childP`, `window`, `end`; `label11` 137–140 | L2099–2127, L3441–3686, L3902–3903, L7234–7302 |
| **DL-12 Coats Without Children** | 200–216 (r6) | carry coat (light), reach peg → bench step, push figure to strip, presence gate (strip + coat), register voices `att_gate_1/2/3`, secret `lostprop` | `attendance`: `art/ch1/dl12.py` (50,182 / 33) | `dl12.coat`, `dl12.peg`, `dl12.figure`, `dl12.strip`, `dl12.gate`, `dl12.splice` (relay) | `school` 200.8; `register` 210.0 (past the gate, L5481) | bed music | L286–296, L5138–5243, L5275–5343, L5381–5408 |
| **DL-13 The Repeated Lesson** | 216–232 (r6) | push figure 2 to the front seat, 12 s lesson cycle (steps, tree, dial), brake, stuck voice loop, gallery (2.05) | `dl13.py` (50,096 / 32) | `dl13.figure`, `dl13.seat`, `dl13.lesson`, `dl13.brake`, `dl13.steps` | `lesson` 216.8 (L5482); `gallery13` 228.4 (y 2.05; L5436) | camera steps back (`k13`) | L5344–5363, L5409–5436, L6595–6596 |
| **DL-14 The Window** | 232–248 (r6) | stair down (5 treads 0.342), pole jam/unjam, crank: paired blinds + clutch grind/sparks, ledges, panel peel, hatch → duct, secret `cupboard` | `dl14.py` (20,089 / 38) | `dl14.pole`, `dl14.crank`, `dl14.blinds`, `dl14.clutch`, `dl14.ledgeA`, `dl14.ledgeB`, `dl14.peel`, `dl14.hatch` | `window` 234.8 (L5483); `hatch14` 234.8 (into the duct, L5484–5487) | cue `child` on the peel | L5283–5286, L5324–5376, L5437–5511, L5633–5653 |
| **DL-14a Lights Out** | 248–263 (r6) | duct exit on bunk 1, bunks/lockers, night-light cycle + brake, crank W1/W2, cord hook (bag holds W1; gown rides up), wall peg (wrong try), eye lamps, door, tannoy `att_rest`, stall hints | `dl14a.py` (45,404 / 65) | `dl14a.nightLight`, `dl14a.brake`, `dl14a.crank`, `dl14a.blinds`, `dl14a.hook`, `dl14a.bag`, `dl14a.gown`, `dl14a.eye`, `dl14a.door` | `dorm` 249.4 (y 1.15; out of the duct, L5648) | — | L5886–5896, L5912–5934, L5974–5986, L6003–6105, L6219–6230, L6327–6345 |
| **DL-14b Unaccompanied** | 263–278 (r6) | escort trolley (patrol, beam, escort), hide in niche/bay, nudge figure out (decoy), stair up to the sick bay (ramp 1.6) | `dl14b.py` (12,898 / 28) | `dl14b.trolley`, `dl14b.figure`, `dl14b.nicheA`, `dl14b.bay`, `dl14b.relay` | `corridor` 263.6 (through the door, L6263) | voice `att_trolley` | L5897–5900, L6106–6135, L6352–6434, L6450–6459 |
| **DL-15 One Pupil Missing** | 278–294 (r6) | sick-bay balcony (1.6), pupil lift (pupil + escort), two figures on a detented rail (two-sided), Mara's chair sit, seat lamps (hers breathes), dismissal, secret `hide15` | `dl15.py` (29,802 / 55) | `dl15.lift`, `dl15.figA`, `dl15.figB`, `dl15.seats`, `dl15.chair`, `dl15.classDoor`, `dl15.flap` | `sickbay` 279.0 (y 1.6; L6264); `class6` 282.7 (L5802); `dismissed` 292.6 (L5733) | `sit15` shot; cue `child` | L5517–5585, L5655–5684, L5709–5736, L5822–5835 |
| **DL-16 After the Bell** | 294–310 (r6) | procession (bow, roll, wait at the edge), held lever → bridge, pit (respawn), rack hooks, latch, counterweight lifts out of the lane, `AfterYou`, tannoy `att_bell`, music hush | `dl16.py` (68,374 / 266; mural 4096×1024) | `dl16.procession`, `dl16.lever`, `dl16.bridge`, `dl16.rack`, `dl16.latch`, `dl16.rackCW` | `crossing` 294.6 (L5803); `store` 300.6 (L5804) | music stops at rack full, bed back at 311 | L5685–5694, L5737–5770, L5797–5798, L5836–5839 |
| **DL-16a Her Way Round** | 310–324 (r6) | gate to pupils, call push, dumbwaiter ride (load 0 after the redesign), stool detent, passage (2.4) and stair down, relay box, 15 s hint | `dl16a.py` (15,438 / 41) | `dl16a.gate`, `dl16a.callPush`, `dl16a.car`, `dl16a.bell`, `dl16a.counterweight`, `dl16a.relay` | `kitchen` 310.6 (L6265) | — | L5901–5904, L5935–5945, L6136–6192, L6233–6246, L6288–6301 |
| **DL-17 A Different Lesson** | 324–345 (r6) | lift the wedged tray, pull drawer, read (records auto-scan), label stamp `FWD WORKS RING A`, test rig (valve, 3 sluices, tank, beds, float latch), stair door, exit to ring A, voice `att_volunteer`, pump relay | `dl17.py` (58,254 / 66; atlas 2048²) | `dl17.tray`, `dl17.drawer`, `dl17.valve`, `dl17.sluiceA`, `dl17.sluiceB`, `dl17.sluiceC`, `dl17.tank`, `dl17.beds`, `dl17.float`, `dl17.latch`, `dl17.stairDoor`, `dl17.pump` | `workshop` 325.0 (L5805) | `drawer17` shot; cue `endAtt` on finish | L5517–5532, L5695–5708, L5773–5794, L5840–5853, L5905–5906, L6193–6215, L6247–6259, L6302–6315, L6461–6469 |

Cross-scene notes: DL-06 and DL-07 share one set and one carrier line (the line belongs to DL-06's Unity scene; DL-07
references it by ID). DL-08 and DL-09's tunnel/balcony come from the same builder (`art/dl04`). DL-09's atrium and the
cut bridge are far backdrop (>30 m wide) shared by DL-09, DL-10 and DL-11.

---

## 6. Data formats and scene definitions

### 6.1 What is authored where

| Data | Authored in | Format on disk | In Unity | Consumed by |
|---|---|---|---|---|
| Geometry, materials, props, movable parts | Blender generators (`art/`) | `.glb` per scene (split the current monolithic `set.glb` by scene) | glTFast import → prefabs | SceneBuilder |
| Colliders (lane boxes, ramps, boards-in-the-air) | Blender: `COL_<name>` empties/boxes with custom props `top`, `onlyFromAbove`, `ramp` | glTF extras + sidecar JSON | `SceneDefinition.colliders` | Core `LaneGeometry` |
| Mechanisms and their parameters | Blender: `MECH_<id>__<part>` objects; parameters as custom props on the `MECH_<id>` root | sidecar `<scene>.scene.json` | `SceneDefinition.mechanisms` (Core DTOs) | Core `MechanismGraph`, Runtime views |
| Lights | Blender: `LGT_<zone>_<name>` empties (type, colour, intensity, range, angle, penumbra, decay, shadow, curve id) | glTF extras (not `KHR_lights_punctual`: the pool needs proxies) | `LightProxy` components | `LightPool` |
| Camera framing zones and authored shots | Blender: `CAM_<zone>` empties (x0, blend, volume, fit width, cx range, fog); moments as keyframe lists | sidecar JSON; moments in Timeline assets | `FramingTrack`, Timelines | U-13 |
| Checkpoints | Blender: `CHK_<name>` empties (x, y, order) + trigger rule id | sidecar JSON | `CheckpointDef` | Core Save |
| Story placements (letters, slots, curios, secrets, voice players, tannoys, emitters, waters, glint anchors) | Blender empties `MECH_Letter_*`, `MECH_Curio_*`, `MECH_Secret_*` (with path points), `MECH_Voice_*`, `MECH_Water_*` | sidecar JSON | Core `Story/*` data | Core |
| Tuning (motor, camera rig, White, audio levels, quality tiers) | Unity | ScriptableObjects wrapping Core POCOs | — | Core + Runtime |
| Text (voice lines, letters, end cards, UI) | repo `data/strings/*.json` | JSON | string tables | UI, VoicePlayer |
| Clip table (names, frames, loops) | generated from `d17.glb` | asset | `ClipTable` | Core acts, Runtime Animator |
| Music cue metadata (handover, intro bars, levels, loop region) | `art/music/prologue_music.json` + `HAND`/`LEVEL` tables | JSON | `MusicCueTable` SO | MusicDirectorModel |

### 6.2 Rules

- **Scene definitions are JSON emitted by the same Blender Python that places the objects**, so positions are never
  typed twice. The Editor importer validates them (`SceneDefValidator`: every `MECH_` part exists, IDs unique, links
  resolve, no overlap-audit hit) and writes a `SceneDefinition` ScriptableObject holding `[Serializable]` Core DTOs.
  Core tests read the same JSON with `System.Text.Json` (tests only); Runtime never parses JSON at play time
  (IL2CPP/AOT safe, no reflection serializers).
- Mechanism behaviour is C# in Core, one class per mechanism *type*; scenes only instantiate types with parameters.
  Bespoke one-offs (DL-05's weigh bands, DL-17's crossed feeds) are parameters (`bands`, `feeds`), not scripts.
- Names: the prototype resolves ≈310 Blender object/material names as string literals in code (plus the 206 keys of the material tables) (e.g. `GoodsPlatform`, `Att16Bridge`, L1383–1386,
  L3040–3042, L3991–4012, L5141–5148). U-12 renames the movable ones to `MECH_<id>__<part>` in the generators and keeps a
  mapping table (`docs/unity/name_map.csv`, generated) from old to new names for the port period.
- `SceneBuilder` regenerates `Assets/Scenes/DL-xx.unity` from the definition: instantiates the GLB prefab, merges static
  dressing by material (static batching), adds `MechanismView`s, `LightProxy`s, colliders for Unity-side queries
  (raycasts for camera occlusion only), and registers the scene's IDs. Hand edits to generated scenes are lost by design.

---

## 7. Additive streaming: no cut between scenes

The prototype is one lane with everything loaded and per-mesh x-culling (±18 m around the camera, refreshed every
100 ms, L8421–8453, L8480). The port keeps **one continuous world coordinate system** and streams scenes additively:

| Piece | Content |
|---|---|
| `DL_Persistent` | SimDriver (Core), D-17, camera rig, LightPool, MusicDirector, VoicePlayer, UI, input. Never unloaded. |
| `DL-01` … `DL-17` (20 scenes incl. 14a, 14b, 16a) | geometry, mechanism views, light proxies, emitters for that x-range, at world positions (no re-centring; max x 345 m keeps float precision ≈ 0.03 mm) |
| `DL-09_Atrium` | the far backdrop (>30 m wide meshes, 88,923 tris), loaded with DL-09 and kept through DL-11 |

- **Core state is global**, not per Unity scene: every mechanism exists in Core from the start of the chapter, so
  unloading a scene never loses state and walking back (e.g. DL-04 → DL-03) is consistent. A Unity scene is only a view.
- **Window:** keep loaded every scene whose x-range intersects `[cam.x − 30, cam.x + 45]` in the direction of travel
  (cull margin 18 m + the widest framing, 12.2 m, + load time at run speed 1.6 m/s). Load with
  `SceneManager.LoadSceneAsync(…, Additive)` and a time-sliced activation budget (`Application.backgroundLoadingPriority
  = Low` during play); unload with a 30 m hysteresis.
- **Seams that must not cut** (walk-through transits): DL-01 → DL-02 passage (L2129–2157: preload DL-02 when the bulkhead
  opens), DL-05 → DL-06 corridor, DL-07 → DL-08 doorway, DL-09 tunnel → balcony, DL-10 → DL-11 counterweight ride
  (DL-11 loaded before `ride10` can be offered), DL-14 → DL-14a duct, DL-14b stair → DL-15 balcony, DL-16a stair → DL-17.
- **Chapter seam:** the prologue ends on an end card, then chapter 1 starts at x 200 (L8178–8196, L8402–8411); a
  loading screen there is acceptable (as in the prototype).
- **Checkpoint load / respawn:** behind the existing fade (1.3 s) or death cut (0.6 s): load the checkpoint scene and
  its neighbours synchronously if not resident, then `ResetFor(checkpoint)` on all mechanisms.
- **Lights and shaders:** proxies register on scene load; the pool's real lights never change count, so loading a scene
  never compiles shaders (the ShaderVariantCollection is warmed at boot, §4.1).
- **Culling inside a scene:** Unity frustum + per-renderer distance culling (`CullingGroup`) with the prototype's special
  rules: couriers only after the reveal or at the gate (L8438), heap only 69–86 (L8439), Up Only's lobby hidden until
  the city shot has left frame (L8443–8449), the reader's remains only near the gap (L8433).

---

## 8. Performance budgets

### 8.1 What the web build has (measured from the assets, and from the code)

| Asset | File | Mesh nodes / draw primitives | Triangles | Materials | Images (Mpx) | Texture RGBA8 + mips | Other |
|---|---|---|---|---|---|---|---|
| `set` (prologue) | 33.5 MB | 777 / 1,314 | 596,846 | 288 | 113 (34.2) | 182 MB (BC7 ≈ 46 MB; ASTC 6×6 ≈ 20 MB) | largest 1536×768, eight 1024² |
| `attendance` (chapter 1) | 22.3 MB | 224 / 624 | 350,537 | 99 | 18 (22.7) | 121 MB (BC7 ≈ 30 MB; ASTC 6×6 ≈ 13 MB) | 4096×1024 mural, 2048² atlas |
| `d17` | 4.4 MB | 35 / 64 | 56,282 | 21 | 3 | 3.3 MB | 1 skin, 26 joints, 76 clips |
| `couriers` | 0.5 MB | 3 poses / 48 | 15,027 (≈5,000 per pose) | 16 | 0 | 0 | 57 slots → ≈ 280k tris instanced in DL-04 |
| `white` | 0.8 MB | 1 / 3 | 4,908 | 3 | 1 | 1.4 MB | 10 clips |

Runtime facts from the code: 54 shader programs after the pool (247 before) (README L27–28); light pool 10 point + 4
spot + 2 shadowed spot + 2 directional + 2 hemisphere (L8542); ≤ 2 shadow maps at 512² (work lamp 1024²); culling
±18 m every 100 ms; heap = 2 instanced draws (1,700 + 600 boxes); dust 1,000 points; sparks 96; steam 34; ripples 25;
glints 10 sprites + 2 lamps; adaptive pixel ratio 0.6–1.5 targeting 55–60 fps on an ordinary laptop
(`docs/direction.md` *Performance budget*). Lit light proxies at once (static count): DL-01 ≈ 14, DL-02–04 ≈ 23,
Ration Hall ≈ 17, DL-06/07 ≈ 17, DL-08/09 ≈ 20, Up Only ≈ 30, DL-11 ≈ 28, chapter 1 ≈ 68 (all of region 6 at once,
the pool picks the nearest). Estimated draws per frame in the densest windows (DL-06/07, DL-11, DL-04 with couriers):
≈ 300–420 before shadow passes (set primitives in a 36 m window + D-17 64 + couriers 48 + heap 2 + FX).

### 8.2 Budgets per tier

| Budget | Switch handheld | Switch docked | PC |
|---|---|---|---|
| Output / internal resolution | 1280×720; dynamic 70–100% (floor 896×504) | 1920×1080 output; internal 1600×900, dynamic 67–100% | native; render scale 1.0 (0.5–2.0 option) |
| Frame rate / frame time | 30 locked / 33.3 ms | 30 locked / 33.3 ms | 60+ / 16.6 ms (120 optional) |
| CPU main thread | ≤ 14 ms (Core 2 steps ≤ 2 ms) | ≤ 14 ms | ≤ 6 ms |
| GPU | ≤ 30 ms | ≤ 30 ms | ≤ 12 ms on a GTX 1060-class GPU |
| Draw calls (batches) visible | ≤ 250 | ≤ 300 | ≤ 1,000 |
| SetPass calls | ≤ 60 | ≤ 70 | ≤ 200 |
| Triangles drawn (incl. shadow casters) | ≤ 300k | ≤ 450k | ≤ 2M |
| Real lights in the pool | 6 point, 3 spot, 1 shadowed spot, 1 directional; hemisphere → ambient per zone | 8 point, 4 spot, 2 shadowed spot, 1 directional | 10 point, 4 spot, 2 shadowed spot, 2 directional (Forward+) |
| Per-object additional lights | 4 | 6 | 8 |
| Shadowed lights | 1 spot, 512² tile (1024² atlas), hard/1-tap | 2 spots, 512² tiles | 2–4 spots, 1024² tiles, soft |
| Texture memory resident (streaming window) | ≤ 160 MB, ASTC 6×6, max 1024² (UI 2048²) | same assets as handheld | ≤ 600 MB, BC7, max 2048² (4096² murals) |
| Mesh memory resident | ≤ 120 MB | ≤ 120 MB | ≤ 400 MB |
| Shader variants built | ≤ 120 | ≤ 120 | ≤ 300 |
| Post | LUT tonemap, vignette, bloom ¼ res; no grain, no MSAA | LUT, vignette, bloom ½ res, grain | LUT, vignette, bloom ½ res, grain, optional SMAA |
| Particles alive | ≤ 600 (dust 300) | ≤ 800 | ≤ 2,000 |
| Real audio voices | 24 | 24 | 48 |
| D-17 | LOD1 ≈ 20k tris | 56k (LOD0) | 56k |
| Dormant couriers (DL-04) | ≈ 1.5k tris per instance, impostor beyond 8 m, no shadows | ≈ 2.5k tris | 5k (as now) |

Grounding: the densest web windows (≈ 300–420 draws, up to ≈ 450k tris in DL-04) exceed the handheld budget, so U-12's
builder must merge static dressing per material per scene (the 1,314 set primitives are mostly static) and add courier
and D-17 LODs; textures are already small (57 Mpx for the whole game ≈ 33 MB in ASTC 6×6), so texture memory is spent
on baked worn masks if option (b) of §4.3 is chosen. No lightmaps: lights flicker, pulse and switch (keep realtime).

---

## 9. Prototype defects and dead code found during the read (decide; do not port blindly)

| # | Line | Finding | Port decision proposed |
|---|---|---|---|
| 1 | L5877 | DL-17's framing volume `v = lerp3(v, fit([6.6,1.6,1.1], 9.4), k17)` is inside a `//` comment, so DL-17 keeps DL-16a's volume | restore it (director to confirm framing) |
| 2 | L5179 | a DL-12 spot over the strip and gate, `S(0xfff0e0, 6, 5, [208.6, 2.6, 0.8] …)`, is inside a comment: never built | ask the director; default: build it |
| 3 | L2213 | DL-03 plate lamp `shadow.bias = -0.001; shadow.radius = 4` inside a comment | apply in Unity |
| 4 | L5919 | DL-16a `mt: 0, flashAt: -9, overAt: -9` inside a comment; `F.mt` starts undefined | initialise explicitly |
| 5 | L3492 | `refs.termLight = refs.dl05Lights[5]` is the bedroom fill (base 2.4), not the terminal light (index 6, base 0); the fill dims to 0.5/1.6 and the terminal light never lights | use the terminal light |
| 6 | L5904, L5982–5985 | DL-16a `need: 0` and no loading offered: the tins, books and stool (`ITEMS16a`, `pushable16a`, `books16a`) are unused; README L161–163 still describes one tin as the line | confirm the redesign; drop the unused items |
| 7 | L5705, L5999 | DL-17 sets `f17.key` after reading, but the valve needs no key (`valveLocked` act unreachable); README L164 still mentions the T-key | follow the code; drop `valveLocked` |
| 8 | L2933, L2898, L3422–3425 | `routeShotAt` written never read; `refuse` act never started; the look-back trigger is cut | do not port |
| 9 | L8073 | the opening card holds 9.5 s (README says 12.5) | follow the code |
| 10 | L7715 | `watchLoad` eases by `1/60·1.2` per frame regardless of dt (frame-rate dependent); all `min(1, dt·k)` easings are dt-approximate | exact damping in Core |
| 11 | L2666, L3130, L3144, L7136, L1501–1504 | gameplay-relevant `Math.random` (crate type and spacing, White patrol targets, payloads, grit) | `SimRng` seeded per run |
| 12 | L8003–8004 | checkpoints `window` and `hatch14` share x 234.8; `hatch14` reloads on the floor, not in the duct | make `hatch14` the duct exit (or drop it) |
| 13 | L2182 | courier slots are matched as `CourierSlot[ABC]…` after three.js strips `.` from `CourierSlot.A.0`; glTFast keeps raw names | normalise names in `NameConventions` |
| 14 | L1467 | the relay lamp's shadow is off on touch devices (look differs by device) | tie to quality tier |
| 15 | L5466–5467 | jam light pulse and pole glow were disabled by the 23 Oct playtest but the code paths remain | port only what is live |

---

## 10. Risks and open questions for the director

1. **The worn-paint look is a per-pixel procedural shader** (3-octave fbm, object space, L386–391, L493–523) on every
   worn surface. Port it as a URP shader (exact look, ~100 ALU/pixel, risky at 720p/30 on Switch) or bake it to textures
   in Blender (cheap, but the look moves into the art pipeline and costs texture memory)? Proposed: shader on PC, baked on
   Switch; needs a side-by-side approval at handheld size.
2. **All sound effects and every voice line are synthesized at runtime** (≈ 60 one-shots, 9 loops, a placeholder
   murmur; no recordings exist in `assets/voice/`). Proposed: bake them offline from the same WebAudio code for parity,
   then hand over to a sound designer. Who owns final SFX and the voice recordings, and when?
3. **AgX tone mapping and the directed moments' audio clock are not native to URP/Unity.** AgX needs a LUT matched by
   eye; the cue clock needs `dspTime` plus a measured output latency per platform (the design tolerates −45/+125 ms,
   `docs/directed_moments.md` rule 4). Switch latency is unknown until a devkit is available.
4. **Gameplay timing is written in animation frames** (act events at clip frame 13/14/22/39…). Core will own a clip
   timeline generated from the GLB; any re-export of D-17's clips changes gameplay. Proposed: freeze clip lengths per
   milestone and test them (ClipTable diff in CI).
5. **Lights live only in code** (≈ 160 proxies with hand-tuned values, none in the GLBs). Moving them into Blender as
   `LGT_` empties makes art the source of truth but is a large one-time migration; confirm that Blender owns lights.
6. **Scene boundaries are not clean in the prototype** (DL-06/07 share a space and a mechanism; DL-08/09 share a builder;
   the atrium spans three scenes; `sceneName` boundaries for chapter 1 are hard-coded x values). Confirm the Unity scene
   cut list in §5/§7, including whether DL-14a, 14b and 16a get their own Unity scenes (proposed: yes).
7. **Switch budgets need geometry work** before any profiling is meaningful: 56 dormant couriers ≈ 280k tris, D-17
   56k tris, 1,314 unmerged set primitives. LODs and static merging are part of U-12, not later polish.
8. **Determinism vs the web sim:** porting to a fixed 60 Hz step with exact damping and seeded randomness will shift some
   timings (e.g. crate spacing, White patrols). Is "mechanical times within ±5% of `tools/sim`" the acceptance bar for
   U-18, or must individual runs match?
9. **README and code disagree** after the 23 October redesign (DL-16a ballast, DL-17 key, opening card length; §9 rows
   6, 7, 9). The port follows the code unless the director says otherwise.
10. **Not in the prototype at all:** the attendant, support transfer and the partner rule (full_game_plan §5). U-10
    will design these from the plan only; the escort trolley is the nearest working reference.
11. **Accessibility gaps** to decide for console certification: the relay pulse and arcs need a photosensitivity check
    (calm mode exists), held-Use (DL-16) needs a toggle alternative, subtitles need size/background options, and the
    keyboard-centric key-cap glyphs need per-platform button prompts.
12. **Chapter 1 sets are still churning** (three redesigns in October). Port the prologue first (U-20/U-21) and freeze
    chapter 1's design before U-22.
