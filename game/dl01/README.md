# DL-01 The Wake: playable prototype

A browser-playable build of scene 1, following `docs/scenes/DL-01_the_wake.md`. It uses D-17 and
the set from Blender, and the gameplay code mirrors the mechanisms planned for the Unity build.

## Run locally

```sh
cd game/dl01
python3 -m http.server 8765
# open http://127.0.0.1:8765/index.html
```

three.js 0.169.0 loads from jsDelivr. The models are in `assets/` as `.glb`, and also as `.json`
(base64-wrapped GLB), because the artifact host serves `.json` but not `.glb`.

## Controls

| | Keyboard | Gamepad |
|---|---|---|
| Move | A D, or the arrow keys | Left stick or D-pad |
| Jump | Space (also W or Up) | A (south) |
| Use | E (or Enter) | X (west) |
| Pause | Esc (or P) | Menu |
| Back to checkpoint | R | (in the pause menu) |
| Developer overlay | ` | |

On touch devices, on-screen buttons appear once play begins.

## What is implemented

**Opening (frames 0–480):**
- The authored D-17 Opening clip.
- Parcel lamp flicker, the relay's three-lamp pulses (D-17's chest lamps answer the second), cradle sparks, the work lamp coming on, eye glints.
- Grit shaken loose by the relay click.
- A camera move from the parcel label out to the side-on view.
- Synthesized sound cues. Skip appears after 1.5 s.

**Movement (decision D1 scale):**
- Walk 0.45 m/s; crouch-walk 0.3 m/s when the ceiling drops below 0.8 m.
- Jump apex 0.4 m, with 100 ms coyote time and a 120 ms input buffer.
- A head bonk under low ceilings.

**Mantle:** jump within about 0.45 m of the crate face, or catch its edge mid-air. This works from either side.

**Latch:**
- Press Use near the T-handle. D-17 crouches into place and heaves twice; the latch gives on the second heave.
- The counterweight drops, the chain runs, and the shutter swings up.
- D-17 flinches, then peeks.
- The solved state becomes the checkpoint.

**Hints:**
- After about 6 s idle near the latch or the crate, D-17 looks at it; after about 12 s he leans toward it.
- With the stuck-prompt option on, a key glyph appears after about 20 s.

**Antenna:** bends back under the shutter instead of passing through it.

**Options:** sound, stuck prompts, and reduced flicker (relay pulses become slow fades, and sparks and lamp flicker are removed).

**Exit:** walking past x = 6.7 m ends the scene and shows the time.

## Rebuild the assets

```sh
cd art/dl01
python build_dl01.py --out ../../game/dl01/assets     # needs bpy 5.2 (Python 3.13)
```
