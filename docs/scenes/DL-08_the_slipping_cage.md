# DL-08 The Slipping Cage: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_plan.md`, scene 8; `docs/chapter1_build_spec.md`, section 6 (18 October 2026)
**Sequence:** DL-07 → DL-08 → DL-09, with no cut on either side
**Duration target:** about 2:00 first time, 1:00 floor (`docs/chapter1_plan.md`)

New in the Chapter 1 rework: the chapter's set piece and finale. Where this plan and the build spec differ, this
describes the game; section 11 lists the differences.

## 1. What the scene must do

| Requirement (plan and overview) | How the build meets it |
|---|---|
| The belt leads to the residential access shaft and an old freight cage | Beyond the top of DL-07's returns belt, three climbs of 0.6 (a hatch housing, a dead conveyor gantry, the upper landing) reach an open freight cage standing level with the landing. Across the shaft and 1.8 m lower, the lit landing leads to the residential tunnel. |
| Halfway, its brake gives: it shudders, then slips | He walks in and it starts down by itself. It settles with a creak, lets down gently for 0.55 m, then shudders (a lurch, a shake, its bulb flickering) and slips, faster and faster. He crouches and grips the side rails (`CageBrace`). |
| The cage has its own pawl lever; throw it as the cage passes the lit landing | A red lever on the cage's left post. Use throws it. A rod runs from its foot to a pawl behind the back mesh, which bites a toothed rack on the shaft wall. It bites only from 0.45 above the lit landing to just below it. Then the cage eases onto the landing with a clunk, the amber lamp steadies, and he straightens (`Proud`). |
| Too early, it rattles; too late, it slides back to the bottom | Too early, the pawl clatters on the rack and the lever springs back; he can throw it again 0.6 s later. Too late, the cage drops onto the buffers with a crash. |
| No death; back in control at once | Nothing fades. After a crash the counterweight hauls the cage back to the top with him in it, and it starts down again 1.6 s later: about 8 s from the crash until it moves again, and about 12 s to the next window. |
| Then the release | The antechamber, then the tunnel, the look back, the hopscotch and the balcony over the chasm city, as built for DL-07 (`DL-07_the_handbrake.md`, sections 2, 6 and 7). |

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
| **The release** | 1:00 | The look back (`LookBack`) and the depot's pulse fading; the hopscotch; the balcony and `Awe`, with `refuge`. Then down the stair to ring C (DL-09). |

## 3. Layout (game x in metres; z is height)

```
x: 85.6 belt top end (deck 1.6)   86.8-87.4 climb 1 (2.2)   87.4-88.2 climb 2 (2.8)   88.2-89.2 UPPER LANDING (3.4)
   89.2-90.8 SHAFT and CAGE (centre 90.0; lever on its left post; rack and pawl at the back right)
   90.8-94.6 LOWER LANDING and antechamber (1.6; ceiling 3.3)   92.75 sign   94.6 tunnel mouth
   96.3 hopscotch   100.0-104.6 balcony   101.3 Awe   104.75 stair down   106.75 ring C (DL-09)
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
- **Shots:** none in the cage. After it, DL-07's `lookback`, `hopscotch` and `vista` (the chapter's one wide shot).

## 7. Sound and music

- **The cage:** a creak as it settles, the chain letting down, a lurch and a shake at the shudder, a groan as it
  slips, a lurch at the catch; the ratchet and the pawl's clatter as it bites, and a clunk at the landing. A crash on
  the buffers; the chain hauling it back.
- **Music:** the depot's bed plays through the cage. It stops in the tunnel, and `refuge` starts at the balcony
  (`DL-07_the_handbrake.md`, section 7).

## 8. Checkpoints

- **cage**: on the upper landing at the shaft's edge (x 88.8, z 3.4), after the climbs and before the set piece.
- **tunnel**: inside the tunnel mouth (x 95.7), with the cage held at the landing. See section 11: the game doesn't
  reach it from `cage`.

## 9. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Latch and hold: twist (a pawl on a moving cage, against time), and the chapter's combine. |
| Builds on | DL-07's pawl (set it when the platform is at the landing) and DL-01's latch; DL-02's climbs. New: timing. |
| Wrong assumption | Throw the lever as soon as it slips, or treat the catch as a stop. Early, it rattles; the catch is the cue. |
| Checkpoints | `cage` before the set piece. A failure needs no respawn: the cage comes back up with him in it. |
| Linkage | Lever, rod and pawl to the rack, seen through the torn mesh; the chain over the sheave to the counterweight. |
| Gear | Set piece (execution), then traversal and the chapter's vista. |
| Curiosity | The hopscotch; the lit window across the chasm (both built for DL-07). |
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
- **The tunnel, the look back, the hopscotch and the balcony** are labelled DL-08 by the game, as the plan has them,
  but built with DL-07 in `art/dl04` and placed by `OFF4`, and the spec lists them under DL-09.
- **Fixed:** the `tunnel` checkpoint used to be set only from `goods` or `latched`, so a restart after the cage put
  him back at its top. `updateTriggers4` now also moves on from `cage`.

## 12. Open questions

- **The window.** About 1.2 s, with a glyph on the lever during the catch. Generous enough for first-time players,
  or should the catch hang longer?
- **The retry.** About 12 s from a crash to the next window, all watched. Shorten the haul and the wait at the top?
- **The cargo lift.** Build it for the balcony, or let the lit window carry the "moving up" idea alone?
