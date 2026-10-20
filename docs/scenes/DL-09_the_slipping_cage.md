# DL-09 The Slipping Cage: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_plan.md`, scene 8; `docs/chapter1_build_spec.md`, section 6 (18 October 2026)
**Sequence:** DL-08 → DL-09 → DL-10, with no cut on either side
**Duration target:** about 2:00 first time, 1:00 floor (`docs/chapter1_plan.md`)

New in the Chapter 1 rework: the chapter's set piece and finale. Where this plan and the build spec differ, this
describes the game; section 11 lists the differences. Pass 2 made the crash a death and added the counterweight's
plates and the tunnel cable: see *Pass 2* at the end.

## 1. What the scene must do

| Requirement (plan and overview) | How the build meets it |
|---|---|
| The belt leads to the residential access shaft and an old freight cage | Beyond the top of DL-08's returns belt, three climbs of 0.6 (a hatch housing, a dead conveyor gantry, the upper landing) reach an open freight cage standing level with the landing. Across the shaft and 1.8 m lower, the lit landing leads to the residential tunnel. |
| Halfway, its brake gives: it shudders, then slips | He walks in and it starts down by itself. It settles with a creak, lets down gently for 0.55 m, then shudders (a lurch, a shake, its bulb flickering) and slips, faster and faster. He crouches and grips the side rails (`CageBrace`). |
| The cage has its own pawl lever; throw it as the cage passes the lit landing | A red lever on the cage's left post. Use throws it. A rod runs from its foot to a pawl behind the back mesh, which bites a toothed rack on the shaft wall. It bites only from 0.45 above the lit landing to just below it. Then the cage eases onto the landing with a clunk, the amber lamp steadies, and he straightens (`Proud`). |
| Too early, it rattles; too late, it slides back to the bottom | Too early, the pawl clatters on the rack and the lever springs back; he can throw it again 0.6 s later. Too late, the cage drops onto the buffers with a crash. |
| No death; back in control at once | Nothing fades. After a crash the counterweight hauls the cage back to the top with him in it, and it starts down again 1.6 s later: about 8 s from the crash until it moves again, and about 12 s to the next window. |
| Then the release | The antechamber, then the tunnel, the look back, the hopscotch and the balcony over the chasm city, as built for DL-08 (`DL-08_the_handbrake.md`, sections 2, 6 and 7). |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **The climbs** | 0:00 | Off the belt's top end, past parcels fallen from the chute from the rings. Three climbs to the upper landing. Checkpoint at the shaft edge. |
| **The cage** | 0:20 | Across the shaft, the lower landing's amber lamp pulses. He walks into the cage. |
| **Down** | 0:25 | It settles (1.0 s), lets down at 0.32 m/s (1.7 s), and shudders (0.7 s). |
| **The slip** | 0:29 | It drops, accelerating, for about 0.9 m, then catches with a lurch 0.35 above the landing and hangs there for 0.75 s. The key glyph shows on the lever. Then it slips again. |
| **The bite** | 0:31 | The window is the hang and the next half second, about 1.2 s in all. Thrown in time: the ratchet, the pawl's clatter, a hard shake, and the cage settles level with the landing. |
| **Or the buffers** | | A crash at the bottom, a heavy shake, 1.4 s of quiet, then the chain hauls it up (about 5 s). It goes again. |
| **Off** | 0:40 | `Proud`. He walks out under the antechamber's low ceiling, past the RESIDENTIAL ACCESS sign, to the tunnel mouth. |
| **The release** | 1:00 | The look back (`LookBack`) and the depot's pulse fading; the hopscotch; the balcony and `Awe`, with `refuge`. Then down the stair to ring C (DL-11). |

## 3. Layout (game x in metres; z is height)

```
x: 85.6 belt top end (deck 1.6)   86.8-87.4 climb 1 (2.2)   87.4-88.2 climb 2 (2.8)   88.2-89.2 UPPER LANDING (3.4)
   89.2-90.8 SHAFT and CAGE (centre 90.0; lever on its left post; rack and pawl at the back right)
   90.8-94.6 LOWER LANDING and antechamber (1.6; ceiling 3.3)   92.75 sign   94.6 tunnel mouth
   96.3 hopscotch   100.0-104.6 balcony   101.3 Awe   104.75 stair down   106.75 ring C (DL-11)
```

**The cage's floor (z):**

| Where | Height |
|---|---|
| Start, level with the upper landing | 3.4 |
| The shudder | 2.85 |
| The catch | 1.95 |
| The pawl bites | from 2.05 down to 1.54 |
| The lit landing | 1.6 |
| On the buffers | −0.1 |

**Rules:**
- **In the cage:** while it moves he can't walk; Use throws the lever. Hauled back to the top, he can step out
  during the 1.6 s before it starts again.
- **The shaft's edges:** he can't step into the shaft unless the cage is at the top, nor out of it on the far side
  unless it is held at the landing. The wall above 3.3 stops him crossing at the upper level.
- **The counterweight** moves opposite the cage, and the sheave turns with it.

## 4. Models (`art/cage/build_cage.py`)

- **The climbs:** the deck beyond the belt; the hatch housing under the chute from the rings; the conveyor gantry,
  dead, with a crate left on its rollers; the upper landing on a patched brick pier, its lattice gate folded back
  and a dead call box. Pipes, a cable tray and a dead lamp along the machine room's wall.
- **The shaft:** guide rails, `CageRack`, `ShaftBuffers` on the pit floor (z −0.6), debris and letters in the pit,
  the head beam with `CageSheave` and a band brake with a frayed cable, and a far glow from the rings above.
- **`Cage`:** a yellow frame with mesh sides, the back mesh torn at its lower right so the pawl and the teeth it
  bites read through the gap; side rails; welded patches; a stop pointer; `CagePawlLever` (red), `CagePawl`, the
  rod between them, `CageChain`, `CageLamp` and `CagePlate`.
- **`CageCounterweight`:** iron slabs in a yellow frame with a hazard band, so it reads passing the cage in the dark.
- **The lower landing:** `LandingStripe` (on the shaft's back wall, the landing's edge, the jamb and the very tooth
  the pawl bites), `LandingLamp` (amber, over the jamb and beside the rack at the stop level).
- **The antechamber:** the RESIDENTIAL ACCESS sign, a notice board, a wall lamp, pipes, a bin and a worn doormat.
- **Clip:** `CageBrace`, 48 frames, looping.

## 5. Lore

| Where | What it says | What it means |
|---|---|---|
| The cage's plate | A cage slipping past a lit landing, the lever thrown, the pawl biting the rack | The one rule, without words. |
| The band brake | Its cable frayed | Why it slips. |
| RESIDENTIAL ACCESS | Rings A, B and C, and an arrow | Where he is going. |
| Parcels on the deck | Fallen from the chute from the rings | The rings' post still comes down. |
| The worn doormat, the notice board | | People came and went this way every day. |

## 6. Camera and light

- **The climbs and the shaft:** from about x 86.0 the framing eases to hold the climbs, the shaft and the lit
  landing together, following him between x 88.2 and 91.4. It doesn't cut or close in while the cage falls.
- **Light:** a cool light over the upper landing; a warm amber light at the lit landing, which pulses until the pawl
  holds and then steadies. The cage's bulb flickers while the brake gives.
- **Shots:** none in the cage. After it, DL-08's `lookback`, `hopscotch` and `vista` (the chapter's one wide shot).

## 7. Sound and music

- **The cage:** a creak as it settles, the chain letting down, a lurch and a shake at the shudder, a groan as it
  slips, a lurch at the catch; the ratchet and the pawl's clatter as it bites, and a clunk at the landing. A crash on
  the buffers; the chain hauling it back.
- **Music:** the depot's bed plays through the cage. It stops in the tunnel, and `refuge` starts at the balcony
  (`DL-08_the_handbrake.md`, section 7).

## 8. Checkpoints

- **cage**: on the upper landing at the shaft's edge (x 88.8, z 3.4), after the climbs and before the set piece.
- **tunnel**: inside the tunnel mouth (x 95.7), with the cage held at the landing. See section 11: the game doesn't
  reach it from `cage`.

## 9. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Latch and hold: twist (a pawl on a moving cage, against time), and the chapter's combine. |
| Builds on | DL-08's pawl (set it when the platform is at the landing) and DL-01's latch; DL-02's climbs. New: timing. |
| Wrong assumption | Throw the lever as soon as it slips, or treat the catch as a stop. Early, it rattles; the catch is the cue. |
| Checkpoints | `cage` before the set piece. A failure needs no respawn: the cage comes back up with him in it. |
| Linkage | Lever, rod and pawl to the rack, seen through the torn mesh; the chain over the sheave to the counterweight. |
| Gear | Set piece (execution), then traversal and the chapter's vista. |
| Curiosity | The hopscotch; the lit window across the chasm (both built for DL-08). |
| Tableau | The chasm city from the balcony: ring C dark and barricaded, light growing toward the upper city. |
| Emotional shot | The city reveal (`vista`), the chapter's one wide shot. |

## 10. Timing

| Phase | Time |
|---|---|
| Walk in to the shudder | about 2.7 s |
| Shudder | 0.7 s |
| First slip, to the catch | about 0.9 s |
| The catch (in the window) | 0.75 s |
| Second slip, to the end of the window | about 0.45 s |
| A crash to the next window | about 12 s |

## 11. Where the build differs from the plan and spec

- **Down, not up.** The plan has D-17 ride the cage up. The spec and the game start it level with the upper landing
  (3.4) and let it down to the lit landing (1.6).
- **No respawn on failure.** The plan makes the cage floor the checkpoint. The game never fades: the cage is hauled
  back to the top and tries again.
- **The cargo lift** (the plan's background event, furniture climbing toward the upper city) is not built.
- **The tunnel, the look back, the hopscotch and the balcony** are labelled DL-09 by the game, as the plan has them,
  but built with DL-08 in `art/dl04` and placed by `OFF4`, and the spec lists them under DL-11.
- **Fixed:** the `tunnel` checkpoint used to be set only from `goods` or `latched`, so a restart after the cage put
  him back at its top. `updateTriggers4` now also moves on from `cage`.

## 12. Open questions

- **The window.** About 1.2 s, with a glyph on the lever during the catch. Generous enough for first-time players,
  or should the catch hang longer?
- **The retry.** About 12 s from a crash to the next window, all watched. Shorten the haul and the wait at the top?
- **The cargo lift.** Build it for the balcony, or let the lit window carry the "moving up" idea alone?

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`: the cage becomes a two-step sequence, a crash kills, and the antechamber gets a
hazard. Positions are game x. This supersedes section 1's "No death" row, section 11's "No respawn on failure" and
the crash-to-retry time in section 10.

**Step 1, the counterweight is too light** (`art/pass2/build_pass2.py`): `CageCounterweight` has lost its top slab;
a tray (`CwTray`) takes its place, and the two plates (`CwPlate0`, `CwPlate1`) lie on the upper landing at 88.55 and
88.95.
- **Short of two plates in the tray,** the cage won't take him. He steps in and it drops a hand's breadth (0.38, or
  0.22 with one plate), the brake squeals and holds, and the alarm bell rings. After about 1.6 s the chain hauls it
  back up, and he startles. He has to step out and in again to try. There is no call button.
- **The plates:** lift one (Use), carry it (slowly, no jumping), and Use within 0.7 of the tray (89.45) while the
  cage is at the top. He turns to the counterweight behind the lane and sets it in (`SetDownHigh`). The plates ride
  with the counterweight from then on.
- Once both are in, they stay in through a respawn at `cage`.

**Step 2, the ride down:** as in sections 1 to 3, with the same speeds and pawl window. The plan's faster ride with
the heavier counterweight is not built.

**The crash is a death:** the cage hits the buffers in its own sump (`CageSump`, water at 0.05) with a splash.
`DeathFall`, the cut, and he is back at `cage` on the upper landing, about 1.5 s after the crash. The White is not in
this water (the plan had the cage over DL-08's sump, and the White taking him).

**The tunnel cable** (`TunnelCable` over `TunnelWet`): in the antechamber at the lit landing's level (1.6), before
the tunnel mouth (94.6), not in the tunnel. A downed cable over a wet patch (92.85 to 94.3) arcs in two places in
turn, every 2.4 s:

| Arc | Deadly between | Tell (a crackle, a flicker) | Live |
|---|---|---|---|
| A, from the split insulation | 93.04 and 93.44 | 0 to 0.3 s | 0.3 to 0.75 s |
| B, from the frayed end | 93.77 and 94.17 | 1.2 to 1.5 s | 1.5 to 1.95 s |

- Between them, a raised hatch cover (`TunnelHatch`, 93.42 to 93.72) stays dry: cross A once it dies, wait on the
  hatch, cross B once it dies.
- The first touch in a game throws him back with sparks (`Knockback`). After that, any touch shorts him out
  (`DeathShock`), and he is back at `landing8`.

**Checkpoints:**
- **cage**: unchanged.
- **landing8** (new): on the lit landing (91.3, height 1.6), set once the cage is held there and he has stepped off it.
  The cage stays at the landing and the plates in the tray, so a shock in the antechamber doesn't send him back up.
- **tunnel**: also reached from `landing8`.

**The long hopscotch** (`HopscotchLong`, 288 frames, 12 s; `art/dl04/hopscotch_clip.py`): he taps square 1,
checks over each shoulder that nobody is watching, then plays all eight squares and HOME, wobbling on 6; a hop-turn,
a cheer and a bounce, two hops back, a shrug, and on. It starts by itself at 96.3 the first time. Moving left or
jumping in its first 76 frames (about 3 s) cancels it. The `hopscotch` shot is close and low while he checks (he
glances into the lens), cranes up to about 45° over the whole court for the hops, then comes down and in for the cheer.

**Curiosities** (both later ones: no light pool or glance):

| Curiosity | Where D-17 stands | What happens |
|---|---|---|
| Hopscotch | The chalk, 96.15, once he has played it | Use plays the long hopscotch again, with its shot. |
| Coin viewer (`CoinViewer`, `CoinViewerHead`, `CoinViewerStep`) | 102.6 on the balcony, facing right | `LookViewer`, about 7 s. He climbs the step, pats his compartment for a coin (there isn't one), presses the plunger anyway: clunk. Up to the eyepieces, and the `viewer` shot looks through them: a 110 mm lens across the chasm to the lit upper city, swinging as he swings the viewer. He stops dead on something, and his antenna wiggles. The plan's cargo lift is not built. |

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`, section 3: the cage made readable. This was DL-08. The director found the cage
puzzle confusing; its two steps stay, and each is now shown before it is asked for.

**Positions:** 12 m further right than in *Pass 2* above (`OFF3` 33, `OFF4` 42). The belt's top end is at 97.6, the
upper landing 100.2 to 101.2, the shaft and cage 101.2 to 102.8, the lit landing and antechamber 102.8 to 106.6
(the cable's arcs 105.04 to 105.44 and 105.77 to 106.17, the hatch cover between), the tunnel mouth 106.6, the
hopscotch 108.3, the balcony 112.0 to 116.6 and the coin viewer 114.6. The balcony's deck runs on as a porch to
118.8, where DL-10 Up Only begins; the stair down to ring C is gone.

**Step 1, the counterweight** (`art/pass3/build_lore.py`):
- **The balance gauge** (`BalanceGauge`, `BalanceNeedle`): a dial on a post at the upper landing's left end (100.3),
  with two pans drawn on it, the counterweight's on the left and the cage's on the right. With the tray empty its
  needle sits deep in a hatched "too light" arc. Each plate in the tray moves it half the way back, and with both it
  stands upright: balanced. When the cage dips under him, the needle kicks.
- **The tray lamp** (`TrayLamp`, in a caged shade on the shaft's back wall, with its own point light): the
  counterweight's open tray hangs in plain view beside the landing, lit, and the two plates lie in its pool.
- **The plates** can't be set down inside the cage; held near the tray, they go in.

**Step 2, the pawl:**
- **He rides braced with his claw on the pawl lever** (`CageRideLever`, 48 frames, looping) from the moment the cage
  settles. Use plays a visible pull (`CagePullPawl`, 18 frames): braced to frame 3, the lever through its throw by
  frame 9, a little past, held. The game drives the lever from the clip, so the pull is seen.
- **The mark:** white chevrons on the shaft's back wall at the lit landing's level (`LoreChevrons`), and one on the
  cage's right front post at its floor (`CageMarker`). The two line up when the floor is level with the landing.
- **The landing lamp** blinks faster as the cage comes down toward it (over its last 1.2 m), and steadies once the
  pawl holds.
- **A miss** still kills: the cage hits the buffers in its sump. The respawn is at `cage` on the upper landing, with
  the plates still in the tray.

**Other fixes:**
- **The look back is cut.** With the cage and the cable behind him, the pan back from the tunnel no longer read as
  the depot. He walks on to the hopscotch.
- **The coin viewer is his:** at the eyepieces, left and right swing it slowly; Use or Jump steps away. Before, it
  panned by itself, too quickly.
- **Use without red** (`docs/direction.md`): the cage's pawl lever is worn steel (`HandledSteel`), the plates and tray
  bare worn iron (`WornIron`), the coin viewer brass.

**Lore:** `LoreBelongings`, a pram wheel and a tied bundle left against the back wall of the lit landing (103.95).

**Checkpoints:** `cage` at 100.8, `landing8` at 103.3 and `tunnel` at 107.7; otherwise unchanged.

## Pass 4 (built 20 October 2026)

From `docs/chapter1_pass4_plan.md`. Positions are game x.

**The cut bridge** (`art/pass4/build_story_shafts.py`, the `AtriumCutBridge*` objects). The way up was cut, on purpose.
- From ring C's lip on the atrium's left wall, a stepped lattice-girder bridge on masonry piers climbs out across the
  void toward the upper rings and the city. Its middle 24 m are blown out.
- **The near stump** is barricaded with beds, doors and timbers, the checkpoint's boom still down, and heaped with
  belongings. On the last portal over its broken end a board, turned to the balcony: GRADE 1–2 BEYOND THIS POINT.
- Twisted girders, torn deck and cables hang from both stumps; a length of the fallen truss lies across the old
  viaduct below.
- **The far stump** still has its lamps lit, and runs into a lit gatehouse in the right wall.
- **Seen:** in the awe shot's crane out over the atrium, through the coin viewer, and from the balcony. The balcony's
  framing is raised so the near stump is in it. It is far detail: plain atrium materials, faces toward the balcony
  only, no shadows, shown with the atrium (from the balcony only).

**His label:** once he has stood in awe at the rail, walking on along the balcony (past 114.9) he checks his label
the first time, looking down toward ring C, and the camera goes in close on it.

**The way on:** RING C ↓ sprayed on a steel sheet wired to the porch rail at the balcony's end, by the lobby's
entrance (`WayRingC09`, `WayRingC09Sheet`, 118.32).

**Echo:** DL-10's lobby carries this scene's balance gauge (see DL-10's *Pass 4*).

**Checkpoints and hazards:** unchanged.

## Pass 5 (built 20 October 2026)

See `docs/chapter1_pass5_plan.md`.

- **The cage plates** show at last. Since pass 2 they had been drawn 3.4 m above where they sat, so he seemed to carry
  nothing.
- **The city** is dark: a few lamps, more ruin and overgrowth.
