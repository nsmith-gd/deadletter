# Undelivered (DL-01 to DL-03): playable prototype

A browser-playable build of the first three scenes of chapter 1, played as one continuous level with no cut between
them. It follows the scene plans in `docs/scenes/` and the standing direction in `docs/direction.md`. It uses D-17 and
the set from Blender, and the gameplay code mirrors the mechanisms planned for the Unity build.

## Run locally

```sh
cd game/undelivered
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

Auto-run is on by default; turn it off in the title or pause menu and Shift runs instead. Sound and
Music have separate toggles. On
touch devices, on-screen buttons appear once play begins.

## DL-01 The Wake, left to right (about 12 m, 3 to 4 minutes)

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
   - He walks through the door, along a service passage behind the wall, and steps out into DL-02.
     The camera follows the whole way, with no cut.

**Movement:**
- Walk 0.9 m/s, run 1.6 m/s, crouch-walk 0.5 m/s.
- Jump apex 0.4 m, with 100 ms coyote time and a 120 ms input buffer.
- Ledges between 0.24 and 0.62 m are climbed rather than jumped.

**Hints:** after about 5 s idle near the next useful thing, D-17 looks at it; at about 10 s he leans in. With the
stuck-prompt option on, a key glyph appears at about 18 s.

## DL-02 The Weight of the Job (about 14 m, 4 minutes)

1. **The weighing room.** Standing on the floor plate lifts the gate, and stepping off drops it. A gauge on the gate post
   reads the load on the plate, and a sign shows the rule.
2. **The weight and the trolley.**
   - Neither the sorting weight nor the trolley is heavy enough on its own.
   - Use to lift the weight. He carries it slowly, and Use again sets it down, onto the trolley's deck if it is in front of him.
   - Use at either end of the trolley to take hold, then push or pull it. Use or Jump lets go.
   - Park it, with the weight, on the plate.
3. **The reveal.** The rack lights come on row by row over 55 dormant couriers like D-17, and the camera widens.
   Climb over the trolley (the weight is a ledge) and walk under the gate.
4. **The recharge hall.**
   - As he walks in among them, he stops and understands (`Realise`) while the music swells.
   - He walks on slowly past the racks, with the camera at the couriers' eye level.
   - Optional: Use at the courier slumped by the lane, and he tries to wake it.

## DL-03 Return to Sender (about 20 m, 3 minutes)

1. **The scanner.**
   - It reads his label (room 114) and refuses it: ring C is sealed.
   - The pit of dead letters opens below. He can only walk slowly while he takes it in, and the music swells.
   - Then he checks his label and the theme turns hopeful.
2. **The return line.**
   - Carriers rise at the hatch, stop at the dock and are hauled to the chute.
   - Boarding one bound for the chute is refused, and the points won't move while the belt runs.
   - Stop the belt (red lever), throw the points (yellow lever), restart the belt, and board at the dock.
3. **The gallery.** He rides up the service ramp and hops out over the pit. Walk past the old sorting desk, the stopped clock and the
   day board to the residential access for the end card.

**Checkpoints:**
- DL-01: start, shutter open, hall, door open.
- DL-02: the room, and solved.
- DL-03: scanned, and the gallery landing.

## Music

The score is in `assets/music/` and is composed and rendered by `art/music/compose_dl01.py` (see its
README). It is sparse:
- A cue for the wake.
- A quiet 48 s loop under play.
- A cello cue at the sorting-hall reveal.
- A short threshold cue as the bulkhead opens and D-17 walks through into DL-02.
- A roll call when the rack lights come on, then a full swell as he walks in among the couriers.
- The refusal, a swell over the pit, near silence for the label check, then the theme in F major.
- The full theme at the end of the gallery, ending in a music-box *Happy Birthday* over the end card.

Music has its own toggle in the title and pause menus, and it dips while paused.

## Rebuild the assets

```sh
cd art/dl01
python build_dl01.py --out ../../game/undelivered/assets     # needs bpy 5.2 (Python 3.13); builds DL-02 too
```

This builds DL-02 (`art/dl02`) and DL-03 (`art/dl03`) too. It writes `set`, `d17` and `couriers` (the dormant couriers' three poses and their rack slots), each as `.glb` and `.json`.
