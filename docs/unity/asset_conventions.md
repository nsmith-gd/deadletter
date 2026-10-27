# Art export for Unity: files, names and import rules (U-12)

**Status:** 26 October 2026, issue #9 (U-12). Design: `docs/unity/port_architecture.md` §0.2, §4.1, §4.3, §6, §8, §9.
**Tools:** `tools/unity_export/` (Blender side), `Assets/DeadLetter/Editor/Art/` (Unity side), Core `Art/ArtNames`,
`Art/TextureBudget`, Runtime `Art/ArtMarker`. Tests: `ArtNamesTests`, `ArtExportTests` (core-tests).

## Summary

- The Blender generators are unchanged, and so is the web build. `export_regions.py` runs `art/dl01/build_dl01.py`'s
  `main()` with its export function swapped for one that records each GLB's objects, then exports the Unity copy from
  that Blender session. Nothing is written to `game/undelivered/assets/`. The sha256 of all 15 files there (4 GLB,
  11 JSON) matched before and after.
- **One glTF per region** (Unity scene), split from the prologue set, plus the far backdrop. **One shared texture
  folder.** The White and the couriers ship as GLBs. D-17 stays the committed GLB (U-11).
- Everything is under the §8.2 budget. All 115 textures (111 set textures plus the characters') together come to 44 MB on
  PC (BC7) and 18 MB on Switch (ASTC 6×6), against window budgets of 600 MB and 160 MB.
- `Assets/Art/` totals 38.4 MB on disk, of which 4.2 MB is the D-17 GLB that was already committed.

## Running it

```sh
DL_NEEDS_BLENDER=1 bash tools/setup/cloud_session.sh       # bpy 5.2.x for python3.13 (≈400 MB download)
python3 tools/unity_export/export_regions.py               # ≈3 min: prologue regions, White, couriers, D-17 check
python3 tools/unity_export/export_regions.py --regions DL-05,DL-06_07    # re-export only what changed
python3 tools/unity_export/export_regions.py --check-web /tmp/web        # also rebuild the web GLBs into /tmp/web and compare
python3 tools/unity_export/report.py                       # sizes, counts, markers, texture budget (no bpy)
```

Then, in Unity: once glTFast has imported the glTFs, the region prefabs build themselves. **Dead Letter → Art → Build
Region Prefabs** rebuilds them all.

**Re-export only what changed.** The generators are not bit-reproducible run to run. Index order varies, and one mesh
(DL-04's `SeatedCourier`) varies by 8 vertices. So every re-export rewrites every `.bin`, and `--regions` keeps commits
small. Textures, sidecars and the glTF JSON are stable. The web build has the same property: rebuilding it under bpy
5.2.3 gives the same nodes, names, materials, images and clip tables as the shipped GLBs, but not the same bytes.

## Outputs (`unity/DeadLetter/Assets/Art/`)

| Path | What |
|---|---|
| `<region>/<region>.gltf` + `.bin` | the region's objects, with the web exporter's settings plus `export_extras` (custom properties → glTF `extras`) |
| `<region>/<region>.art.json` | sidecar: scenes, game region, lane x-range, bounds, counts, markers, materials, textures, driven names, TODO |
| `<region>/<region>.prefab` | generated in Unity by `ArtPrefabBuilder` (commit it like `D17.controller`) |
| `Textures/*.png` + `textures.json` | every set texture once, with its source size and use (color / normal / linear) |
| `Materials/*.mat` | URP Lit materials, one per Blender material name, generated in Unity |
| `regions.json` | index of regions and characters |
| `White/white.glb`, `Couriers/couriers.glb` | web exporter settings, rebuilt by the tool |
| `D17/d17.glb` | unchanged (U-11's copy of the shipped GLB). The tool rebuilds D-17 and checks its 76 clips (names and frame counts): identical. `--write-d17` replaces it. |

New outputs get minimal `.meta` files with stable GUIDs (MD5 of the asset path, the same scheme as Core `StableGuid` and
the audio importer), so references survive a delete and re-export.

**Why glTF + shared PNGs rather than GLB:** a texture embedded in a GLB is a sub-asset of glTFast's importer. It has no
`TextureImporter`, so it can take no per-platform max size or format. External PNGs get one. Sharing the folder also
stores each texture once. It is still one exporter (Blender's glTF), as the issue asked.

## Regions

An object goes to the region its hierarchy's bounding-box centre x falls in, with the cuts taken from index.html's
`sceneName` (L8135–8144). There are two exceptions. An object wider than 30 m goes to the backdrop. A mechanism's objects
always go to their scene's region.

| Region | Scenes | Game region | Lane x | Size MB | Meshes | Prims | Tris | Mats | Tex | PC MB | Switch MB | MECH | CHK |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DL-01 | DL-01 | 1 | < 12.0 | 1.07 | 85 | 104 | 37,328 | 44 | 11 | 4.46 | 2.00 | 16 | 4 |
| DL-02 | DL-02 | 2 | 12.0–25.0 | 2.31 | 75 | 115 | 46,174 | 44 | 10 | 4.81 | 1.92 | 3 | 1 |
| DL-03 | DL-03 | 2 | 25.0–30.6 | 0.31 | 34 | 36 | 10,776 | 22 | 7 | 2.65 | 1.06 | 11 | 2 |
| DL-04 | DL-04 | 2 | 30.6–47.9 | 1.38 | 60 | 94 | 31,606 | 41 | 6 | 1.37 | 0.62 | 6 | 1 |
| DL-05 | DL-05 | 2 | 47.9–59.8 | 2.38 | 53 | 67 | 62,393 | 50 | 14 | 8.30 | 3.22 | 6 | 2 |
| DL-06_07 | DL-06, DL-07 | 3 | 59.8–80.75 | 2.30 | 121 | 166 | 52,988 | 63 | 16 | 6.95 | 2.85 | 20 | 3 |
| DL-08 | DL-08 | 4 | 80.75–97.6 | 0.78 | 91 | 113 | 15,798 | 49 | 17 | 3.71 | 1.53 | 21 | 2 |
| DL-09 | DL-09 | 4 | 97.6–118.8 | 1.43 | 83 | 164 | 33,026 | 66 | 16 | 8.59 | 3.42 | 7 | 3 |
| DL-10 | DL-10 | 4 | 118.8–127.9 | 3.65 | 49 | 155 | 71,820 | 53 | 6 | 4.50 | 2.02 | 17 | 1 |
| DL-11 | DL-11 | 5 | ≥ 127.9 | 4.28 | 94 | 221 | 85,262 | 95 | 34 | 9.44 | 4.25 | 10 | 3 |
| DL-09_Atrium | DL-09–11 (backdrop) | 4 | > 30 m wide | 6.04 | 25 | 59 | 132,919 | 43 | 1 | 0.67 | 0.30 | 0 | 0 |
| DL-12 | DL-12 | 6 | 199.0–216.0 | 2.32 | — | — | — | — | — | — | — | 0 | 2 |
| DL-13 | DL-13 | 6 | 216.0–232.0 | 2.15 | — | — | — | — | — | — | — | 0 | 2 |
| DL-14 | DL-14 | 6 | 232.0–248.0 | 1.05 | — | — | — | — | — | — | — | 0 | 2 |
| DL-14a | DL-14a | 6 | 248.0–263.0 | 1.49 | — | — | — | — | — | — | — | 0 | 1 |
| DL-14b | DL-14b | 6 | 263.0–278.0 | 0.62 | — | — | — | — | — | — | — | 0 | 1 |
| DL-15 | DL-15 | 6 | 278.0–294.0 | 1.44 | — | — | — | — | — | — | — | 0 | 3 |
| DL-16 | DL-16 | 6 | 294.0–310.0 | 1.23 | — | — | — | — | — | — | — | 0 | 2 |
| DL-16a | DL-16a | 6 | 310.0–324.0 | 0.87 | — | — | — | — | — | — | — | 0 | 1 |
| DL-17 | DL-17 | 6 | ≥ 324.0 | 3.04 | — | — | — | — | — | — | — | 0 | 1 |

The prologue rows cover all 777 objects of `set.glb`, plus 22 checkpoints and 4 mechanism anchors. **Chapter 1
(DL-12 to DL-17, from `attendance.glb`'s builder, `--chapter1 --no-prologue`)** adds 9 regions (14.2 MB of glTF + bin)
and 18 textures, with its 15 checkpoints; its mesh and texture columns are not measured yet (`report.py` predates it). Sizes are the .gltf plus the
.bin; textures are counted separately (7.3 MB, shared). The largest texture is 1621×192. Switch caps 7 textures above
1024 px. On PC nothing is capped.

- DL-06 and DL-07 export together. They share one floor, one carrier line and one builder, and the game tells them apart
  by state, not by x (§5).
- The backdrop rule works on whole hierarchies, so it holds 132,919 triangles. §5 counted 88,923, measured per mesh.

## Naming conventions

Core `ArtNames` parses these; the prefixes are case-sensitive. The Unity export renames objects on its own copy only, so
the web build keeps the old names. A renamed object keeps its source name as the custom property `dl_name`, which reaches
the glTF as extras and the sidecar as `source`.

| Prefix | Form | Example | In Unity |
|---|---|---|---|
| `COL_` | `COL_<name>` | `COL_shelf_dl02` | `BoxCollider` fitted to the mesh; renderer and filter removed |
| `LGT_` | `LGT_<zone>_<name>` | `LGT_ration_strip` | empty + `ArtMarker` (LightBuilder, U-15) |
| `MECH_` | `MECH_<Type>_<scene>_<name>[__<part>]` | `MECH_Door_dl01_shutter__ShutterRail` | renderers kept + `ArtMarker` (type, id `dl01.shutter`, part) |
| `CAM_` | `CAM_<zone>` | `CAM_dl01.hall` | empty + `ArtMarker` (U-13) |
| `CHK_` | `CHK_<name>` | `CHK_landing8` | empty at (x, floor height, 0) + `ArtMarker` (`order`, `game_region`, `height`) |

- **MECH:** `Type` is PascalCase with no underscore. The ID is §5's `MechanismId` with `.` written as `_`, because three.js
  strips dots from names (§9 #13). A part keeps its source object's name.
- **MECH roots:** a mechanism made only of parts (relay lamps, cradle arms, the carrier line, the DL-01 scale needle)
  gets an empty anchor named `MECH_<Type>_<id>` at the centre of its parts. The parts are not re-parented.
- **Mapping table:** `tools/unity_export/conventions.py` `MECHANISMS` holds 54 mechanisms over 113 objects, taken from the
  groups index.html moves together. Where U-10 builds a Core class for the mechanism, `<Type>` is that class's name
  exactly (agreed on #9), so the importer binds `MECH_<Type>_…` to it with no lookup table. The DL-07 bucket is a part
  of `BucketGate` (`MECH_BucketGate_dl07_gate__GateBucket`): the Runtime calls `BucketGate.Drop()`. The remaining
  types (Carryable, Pushable, Draggable, Press, Collapse, Scanner, Button, …) are U-11 contracts, hazards or
  scene rules; the scene ports (#16–#18) name them.
- **Name map:** `docs/unity/name_map.csv` is generated. It lists old → new for every renamed object, plus 64 "driven"
  objects. Those are names index.html quotes that match an object and are not yet renamed, such as `CableSpark`,
  `WorkLampBulb`, `SeatedLamps` and `AtriumFanLow`.
- **Duplicate suffixes:** Blender's `.001` and Unity's ` (1)` are ignored when parsing. `ArtNames.WebName` reproduces
  three.js's dot stripping, so `CourierSlot.A.0` becomes `CourierSlotA0`. The courier slots keep their raw names in
  `couriers.glb`.
- **Origins:** most generators build meshes in world space with the origin at 0. A marker's `position` (its origin) is
  therefore often 0. Use its `center` (the bounding-box centre) instead.

## Markers per region: what exists, what is still to author

| Region | CHK (from index.html `CHECKPOINTS`, L7975–8014) | MECH (renamed + anchors) | COL / LGT / CAM |
|---|---|---|---|
| DL-01 | start, shutter, hall, door | shutter, latch, relay\*, crank, door, cart, scale\* | TODO |
| DL-02 | room | press, box | TODO |
| DL-03 | weighroom, solved | weight, trolley, plate, gate | TODO |
| DL-04 | bay | courier, bayPlate, cradle\*, bayDoor | TODO |
| DL-05 | ration, hatch | drum, body, weighIn, hatch, servedFlag | TODO |
| DL-06_07 | scanned, landing, gallery | scanner, stopLever, points, line\*, weight0/1, bucket, gate, collapse | TODO |
| DL-08 | goods, latched | trolley, pan, platform, pawl, belt | TODO |
| DL-09 | cage (y 3.4), landing8 (y 1.6), tunnel | plate0/1, cage, cagePawl | TODO |
| DL-10 | uponly (y 1.6) | case, lift, carPlate, upButton, serviceCrank, serviceDoor, serviceUp, counterweight | TODO |
| DL-11 | ringc, bedroom, forwarded | bell, junction, duct, c114Door, facade, desk, terminal | TODO |
| DL-09_Atrium | — | — | TODO |
| DL-12 to DL-17 | school, register, lesson, gallery13, window, hatch14, dorm, corridor, sickbay, class6, dismissed, crossing, store, kitchen, workshop | **none yet**: `conventions.py` `MECHANISMS` has no chapter 1 rows. Add them with U-10's class names when chapter 1's Core port (#18) names its mechanisms (§5's `dl12.*` to `dl17.*` IDs), then re-export with `--chapter1 --no-prologue --regions …` | TODO |

\* anchor empty.

**Not derived, because it would be neither cheap nor certain.** Every region's sidecar carries this list as `todo`.

- **`COL_`:** lane collision is code (`floorAt`/`surfaceAt`/`ceilingAt`, L1617–1769, L4135–4201, chapter 1's
  equivalents). Author axis-aligned `COL_` boxes in the generators, with custom properties `top` and `onlyFromAbove`
  (§4.6, §6.1).
- **`LGT_`:** every light is created in code: about 160 proxies across L1457–1478, L2209–2221, L3068–3092, L4052–4087,
  L5174–5222 and L7872–7885 (§4.20). This needs the director's call on Blender owning lights (§10 #5).
- **`CAM_`:** framing zones are code (`frameFor`, L7644–7806). Core `PrologueFraming` already holds DL-01 to DL-07.
- **Mechanisms still under source names:** the "driven" rows of `name_map.csv`. Story placements (`MECH_Letter_*`,
  `MECH_Curio_*`, `MECH_Secret_*`, `MECH_Voice_*`, `MECH_Water_*`) and their parameters as custom properties also
  remain.

## Unity import (`Assets/DeadLetter/Editor/Art/`)

| Piece | Does |
|---|---|
| `ArtImportSettings` (AssetPostprocessor) | Textures in `Assets/Art/`, except D17: type, sRGB and normal flag from `textures.json`; mips on; NPOT kept; CompressedHQ. **Per platform**, from Core `TextureBudget`: `Standalone` BC7 at max 2048 (murals 4096), `Switch` ASTC 6×6 at max 1024 (UI 2048). glTF/GLB: glTFast `nodeNameMethod = OriginalUnique`, `animationMethod = Mecanim`, mips, set through `SerializedObject` as `D17ImportSettings` does. After a region's glTF imports, it queues that region's prefab build. |
| `ArtPrefabBuilder` | Instantiates glTFast's imported hierarchy (an unlinked copy; the imported asset is never edited) under `<region>` → `<region>_gltf`. **Turns it 0° or 180° about Y, whichever puts the sidecar's markers at their §0.2 positions**: this is the §0.2 handedness check, measured on every build, with a warning if neither turn fits. Applies `COL_`/marker rules and swaps materials, then saves `<region>.prefab`. |
| `ArtMaterials` | glTF PBR → URP Lit: base colour and map, metallic, smoothness = 1 − roughness, normal map. Emission = `emissiveFactor × KHR_materials_emissive_strength` (HDR) with its map, `_EMISSION` on, realtime-emissive GI. `BLEND` → transparent, `MASK` → alpha clip, `doubleSided` → cull off. |
| `ArtSidecar` | JsonUtility DTOs for `regions.json`, `*.art.json` and `textures.json`. |
| Runtime `ArtMarker` | The marker data on the prefab: prefix, type, id, part, source name, props. |

**Not converted, and why:**

- **Worn shader:** the web build replaces most materials by name with its `WORN`, `PLAIN`, `GLASSY` and `EMIT` tables
  (L383–554). The GLB's own PBR values are mostly placeholders; only 16 of 288 materials emit. That is U-15's
  `MaterialMap`, keyed by the same material names, which is why `Materials/` is one asset per name.
- **Other material features:** decals with polygon offset (`Chalk*`, `RingLetter*`), `KHR_materials_transmission`
  (2 materials) and metallicRoughness/occlusion maps (none today; the builder warns if any appear).
- **Static batching flags, LODs and shadow-caster rules:** these belong to the scene builder, which knows which objects
  mechanisms move.

## Unity APIs not verified here (no editor in the container)

1. **glTFast and external textures.** Whether glTFast imports a `.gltf` whose images are `../Textures/*.png`
   (relative, outside its folder) by using the project's PNG assets or by loading its own copies. Either way the prefab
   ends up with `ArtMaterials`' URP materials, which load the PNGs through `AssetDatabase`.
2. **glTFast field paths.** `importSettings.nodeNameMethod`, `importSettings.animationMethod` and
   `importSettings.generateMipMaps` in glTFast 6.8, as in `D17ImportSettings`. Also whether `OriginalUnique` keeps
   unique names verbatim.
3. **glTFast's main asset.** That `AssetDatabase.LoadAssetAtPath<GameObject>` returns the scene root, and that material
   names equal glTF material names.
4. **Texture platform overrides.** That `TextureImporterPlatformSettings.name = "Switch"` is the right string, and that
   it sticks without the Switch module (the audio importer has the same open question).
5. **Material colours.** That URP Lit material colours need `.gamma` (gamma-stored, linearised in a Linear project),
   and that the hand-set `_Surface`/blend/keyword combination matches what URP's material inspector would set. The
   inspector re-validates when a material is opened.
6. **Building prefabs from `OnPostprocessAllAssets`.** That doing it via `EditorApplication.delayCall` is safe.
7. **glTFast's axis conversion.** Measured at build time rather than assumed.
