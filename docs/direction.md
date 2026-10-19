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

## Colour language: what you can use is red

Anything D-17 can use carries red paint: handles, levers, the crank wheel, the pull-cord's bead, the
sorting weight, the trolleys' grips, the pawl lever, the desk's edge. Nothing else in a scene is that
red. On a phone screen this is how the player finds what matters. Light helps too: a pool of light
over an interactable that would otherwise sit in shadow (the crank wheel).

## Let the player try things

If something looks like it can be climbed into or ridden, let the player do it, even if it ends badly.
The carriers in DL-05 can be boarded anywhere, by Use or by a standing jump beside one (a running jump only jumps,
so hopping over something by the dock never boards a carrier by accident). Riding one to the chute
tips D-17 onto the heap of dead post, and he is back at the checkpoint after a fade.

## Use the camera

One continuous side-on shot is the game's camera, the way Limbo and Inside play as one shot. Gameplay never takes
it away. Framing changes (wider over a puzzle room, closer in a tight space, higher over a drop) blend over one to
three seconds as D-17 moves, and the whole puzzle stays in frame while the player thinks.

**Authored shots are reserved for emotional moments** (`currentShot()` in the game). Each is eased in and back
out, and never shows puzzle information the side view doesn't. In Chapter 1 there are seven:
- **DL-04:** the realisation among the couriers, as the racks light.
- **DL-05:** the scan, the pit and the label check, as one sequence.
- **DL-08:** after the cage, the look back at the depot, and the crane out over the city, which hands back to D-17.
- **DL-09:** the growth marks, the terminal answering, and the rabbit.

The lenses:
- **Low and close for intimacy:** 45 to 55 mm.
- **Wide and high for scale:** 24 to 32 mm, about once a chapter.

Not shots: cranks, levers, lifts, pawls, carts, falls and quirks all play in the side view. A cause and its effect
must be readable in the side view, through a visible cable, rod, light or sound.

**Shake for impacts.** A short, damped shake when something heavy lands, never for footsteps. Calm mode turns it off.

**Cinematics play once.** After a respawn or a checkpoint reload, authored moments the player has already sat
through are skipped. Starting over clears this.

## D-17's quirks

Small reactions for particular moments make him a character rather than a cursor:
- **Attention:** he stands to attention under the scanner, follows the sweep with his head, and deflates at the refusal.
- **Proud:** two little bounces when something works (the bulkhead opening, the points set to the service ramp).
- **PeekDown:** he leans out over an edge he is left at, one claw on the rail: the trench, the crate, the pit rail.
- **BrushOff:** a shake and a brush-down after climbing out of a tub of old post.
- **Startle:** a jolt at a slam or clang close by.
- **Teeter:** knees buckle and claws wheel when something gives under him, then a hop back to safety (the unlatched lift platform).
- **Pat:** a goodbye pat for something that helped and has to stay behind (the goods trolley).
- **LookBack:** at a threshold he won't recross, he turns and looks back at where he came from.
- **Hopscotch:** chalk squares on the floor; he hops them, one foot, one foot, both feet.
- **Awe:** at a view of something vast, he looks up and along it, then down, and holds his parcel.

They are short, and any input cancels them, except where they carry a story beat (the peek over the pit).
Add new ones for new moments rather than reusing an old one for something it doesn't fit.

## Performance budget

The browser build must run smoothly on an ordinary laptop. Keep within these limits:
- **Lights:** at most about a dozen per region. Lights for scenes out of view are switched off while D-17 is hidden (the passage, the scanner corridor).
- **Shadows:** only a few lamps cast shadows, never more than two lit at once, all spot lights (never a point light: that is six passes). Only small props near them cast; walls and floors never do.
- **Materials:** all worn surfaces share one shader program. Background crowds (the couriers) use plain materials.
- **Culling:** set pieces more than about 18 m from the camera are hidden, shadows included. The couriers appear only when they can be seen, and the atrium only from the balcony.
- **Far detail:** distant set pieces (the atrium) are flat and plain: quads for windows and doors, no worn-paint shader, no shadows. The camera's far plane opens up only where the view needs it.
- **Resolution:** it adapts to hold 55 to 60 fps. MSAA is off because the post chain doesn't use it, and the bloom runs at half size.

## Scene length

Scenes earn their length with distinct rooms and beats, never by making a puzzle slower or harder. See
`docs/puzzle_principles.md` for the rules and `docs/chapter1_plan.md` for how Chapter 1 reaches its target.

## Tone

- Timid, curious and whimsical, never slapstick. "Wall-E vibes" for D-17, without borrowing EVE or Wall-E
  iconography.
- D-17 never walks on his arms, and his head is steady when he walks.
- Most players want automatic running, so Auto-run is on by default.

## The refuge's levels

The refuge is an underground city dug into the rock, and the story climbs it. The bottom, where D-17
starts, is the poorest and most industrial: the depot, the returns pit, ring C. It is rushed, patched
and cramped, with pipes, ducts, cables and machinery everywhere. The higher the levels, the closer
they are to the surface and the more polished they become. That gradient is the refuge's class system.
Don't make it a clean, regular silo.

**The look (director's reference):** a whole city in a deep chasm, read in layers.
- **Foreground:** dark cliffs with warm-lit dwellings and workshops carved into them, galleries, pipes, lifts and cranes.
- **Mid-ground:** heavy arched viaducts spanning the chasm at different heights, waterfalls into misty depths, stalactites overhead.
- **Background, higher up:** the grander upper city of domes, towers and chimneys, rising out of cool blue haze.

The light is warm amber against that haze. The first reveal from DL-08's balcony must say that a larger world lies ahead and above. On the poorest levels, homes stay mostly dark; the lights are the city's systems still running.

**Light by level:** abandoned lower levels get very little light: a failing bulb or two, a lamp left on behind a door, light falling from far above. Darkness is the default down there, and a lit room is an event. Light grows with height: sparse on the middle tiers, warm and dense toward the upper city, where people still live. Keep what the player must read (the path, the red interactables) lit, even in the dark.

## World building

Lore is read from the world, never from a log.

- **What carries it:** signs, notices, chalk boards, stamps, pigeonholes and parcels.
- **Text:** short, original and in-world (refuge years, ring and room numbers).
- **The history it must stay true to (GDD):**
  - The refuge was built over a century ago.
  - Births stopped, and the last other resident died nine years ago.
  - Local forwarding terminals keep addresses, and there is no central directory.
