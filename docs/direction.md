# Dead Letter: standing direction

Notes from director review that apply to every scene, not just the one under review. Read this before
planning or building a scene.

## Scenes never cut

Each scene runs straight into the next with no fade, card or load. The camera follows D-17 through
doorways, passages and lifts. When a scene's geometry has to change, change it behind something he
walks past. The only end card in a build is at the end of its last scene.

## Emotional moments: the music swells and the pacing slows

When D-17 understands something (that the couriers are like him and gone, that his address is "not in
service"), the moment must be felt, not just seen.

- **The music swells.** Build to a real climax: strings broadening with violins in octaves, a timpani
  roll and a suspended-cymbal swell into the peak. Then let it go, and leave room for the music box.
  A soft chorale under the moment is not enough.
- **The pacing slows.**
  - D-17 stops for an authored reaction (`Realise`, `CheckLabel`), then walks with the slow `SadWalk`
    while the moment lasts (0.39 m/s, no running).
  - The camera eases more slowly and frames lower or wider.
  - Hold the moment for several seconds before handing back full control.
- **Then something turns.** After the low point, give a small movement of purpose: a check of the
  label, a nod, the theme returning in a major key.
- **Sparseness still holds.** Between these moments, music stays sparse (the GDD's "sparse music at
  transitions"). The bed sits low and puzzles keep their room tone.

## Use the camera

The side-on framing is the default, not a rule. For a moment that matters, the camera leaves it for an
authored shot with its own position, aim and lens, eased in and back out (`currentShot()` in the game):
- **Low and close for intimacy.** Use a 45 to 55 mm lens: his face as he touches his chest among the couriers, the label check.
- **Wide and high for scale.** Use a 26 to 32 mm lens: the crane up and out over the pit, the ride up the ramp with the heap below.
- **Beside him for effort.** At the crank, low behind his shoulder, the door rising ahead.
- **Shake for impacts.** A short, damped shake when something heavy lands (the shutter, the gate, a carrier tipping), never for footsteps. Calm mode turns it off.

Play carries on under a shot where it can, and any shot hands back smoothly.

## D-17's quirks

Small reactions for particular moments make him a character rather than a cursor:
- **Attention:** he stands to attention under the scanner, follows the sweep with his head, and deflates at the refusal.
- **Proud:** two little bounces when something works (the bulkhead opening, the points set to the service ramp).
- **PeekDown:** he leans out over an edge he is left at, one claw on the rail: the trench, the crate, the pit rail.
- **BrushOff:** a shake and a brush-down after climbing out of a tub of old post.
- **Startle:** a jolt at a slam or clang close by.

They are short, and any input cancels them, except where they carry a story beat (the peek over the pit).
Add new ones for new moments rather than reusing an old one for something it doesn't fit.

## Performance budget

The browser build must run smoothly on an ordinary laptop. Keep within these limits:
- **Lights:** at most about a dozen per region. Lights for scenes out of view are switched off while D-17 is hidden (the passage, the scanner corridor).
- **Shadows:** only three lamps cast shadows, all spot lights (never a point light: that is six passes). Only small props near them cast; walls and floors never do.
- **Materials:** all worn surfaces share one shader program. Background crowds (the couriers) use plain materials.
- **Culling:** set pieces more than about 18 m from the camera are hidden, shadows included. The couriers appear only when they can be seen.
- **Resolution:** it adapts to hold 55 to 60 fps. MSAA is off because the post chain doesn't use it, and the bloom runs at half size.

## Tone

- Timid, curious and whimsical, never slapstick. "Wall-E vibes" for D-17, without borrowing EVE or Wall-E
  iconography.
- D-17 never walks on his arms, and his head is steady when he walks.
- Most players want automatic running, so Auto-run is on by default.

## World building

Lore is read from the world, never from a log.

- **What carries it:** signs, notices, chalk boards, stamps, pigeonholes and parcels.
- **Text:** short, original and in-world (refuge years, ring and room numbers).
- **The history it must stay true to (GDD):**
  - The refuge was built over a century ago.
  - Births stopped, and the last other resident died nine years ago.
  - Local forwarding terminals keep addresses, and there is no central directory.
