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
| Move | A D, or the arrow keys | Left stick or D-pad (push fully to run) |
| Walk while Auto-run is on | Hold Shift | Hold B |
| Jump | Space (also W or Up) | A (south) |
| Use | E (or Enter) | X (west) |
| Pause | Esc (or P) | Menu |
| Back to checkpoint | R | (in the pause menu) |
| Developer overlay | ` | |

Auto-run is on by default; turn it off in the title or pause menu and Shift runs instead. On
touch devices, on-screen buttons appear once play begins.

## The scene, left to right (about 12 m, 3 to 4 minutes)

1. **Opening, 20 s.**
   - D-17 wakes in the cradle. The parcel lamp, the relay pulses he answers, sparks, the work lamp, grit, then the camera move.
   - Skip appears after 1.5 s.
2. **Pull-cord lamp.** Optional: the first use of Use. He tiptoes up, tugs the cord, and the lamp warms the
   alcove, revealing a depot route map (depot, homes, school, works, ward, then up).
3. **Shutter.**
   - He crouches automatically under it.
   - Use on the T-handle: two heaves, the latch gives, the counterweight drops and the shutter swings up. He flinches.
4. **Fallen conveyor (0.22 m).** The first jump.
5. **Crate (0.45 m).** Jump near it to climb it. The climb is a 2.3 s authored beat:
   1. He looks up, hops and grabs the edge.
   2. Heave, slip back, heave again.
   3. His old left knee over the edge, then he tips onto the top.
   4. He stands and glances back down.

   The camera pushes in for it.
6. **Drain trench.** Jump it, or fall in and climb out the far wall (a safe failure).
7. **Sorting hall.** The camera pulls back to show the scale: a gantry, columns, a huge backlit sorting carousel,
   chutes, light shafts, a slow searchlight, swaying parcel hooks, a sparking live cable and a steam vent.
8. **Bulkhead.**
   - Use the red crank wheel. D-17 turns his back to the camera and hauls it hand over hand, five strokes, as the door rises.
   - He walks through into depth, toward DL-02.

**Movement:**
- Walk 0.9 m/s, run 1.6 m/s, crouch-walk 0.5 m/s.
- Jump apex 0.4 m, with 100 ms coyote time and a 120 ms input buffer.
- Ledges between 0.24 and 0.62 m are climbed rather than jumped.

**Hints:** after about 5 s idle near the next useful thing, D-17 looks at it; at about 10 s he leans in. With the
stuck-prompt option on, a key glyph appears at about 18 s.

**Checkpoints:** start, shutter open, hall, door open.

## Rebuild the assets

```sh
cd art/dl01
python build_dl01.py --out ../../game/dl01/assets     # needs bpy 5.2 (Python 3.13)
```
