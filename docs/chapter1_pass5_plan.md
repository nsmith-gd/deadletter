# Chapter 1, pass 5: time, cause, and a world gone dark

**Status:** built, 20 October 2026 (see *Status: built* at the end). These are the director's notes from playing pass 4 (Version 15).

**Liked:** the falling letters and the mail slots; dragging a body onto the weigh-in ("quite dark"); the EVERYONE UP graffiti (in moderation); the two weights watched into the bucket; the flooded architecture; the hopscotch; the neighbourhood; the label close-up at C-114.

## 1. The story's frame

**Why D-17 wakes, said in words.** The game opens on a short title card before the wake:

> The lower rings of the refuge have been dark for seventy-six years.
> Tonight the power came back on. Nobody left down here could say why.
> In the depot, one courier still had a parcel to deliver.

It sets up three things:
- the time (76 years);
- the mystery (who restored the power, and why, is the story's thread toward the regeneration at its end);
- the mission.

**The timeline is consistent.**
- The parcel was for Mara's ninth birthday: nine growth marks.
- The lower rings collapsed that year, and nobody has lived down here since.
- So the dead are 76 years dead: skeletons in the clothes they died in, dust, nothing fresh.

## 2. What killed them, shown

Every body has a visible cause.

| Where | Cause | How it's shown |
|---|---|---|
| DL-02, the sorters at their posts | The air was cut. The upper grades diverted the lower works' air to rings A and B, and the night shift suffocated at their work. | An AIR · RINGS A–B PRIORITY notice; the depot's air gauge on zero; the bulkhead to the stairs welded shut, with scratch marks at its foot. |
| DL-05, the Ration Hall | Famine. | As built, aged to bones under the sheets. |
| DL-08 | The goods lift fell. | As built. |
| DL-10 | The crush at the last car. | Household belongings left behind, not shoes. |
| DL-11 | The flood. | As built. |

## 3. Fixes from play

- **The cage plates:** they were invisible, drawn 3.4 m too high since pass 2. That is why the cage made no sense.
- **The light pop at ring C's seal:** ring C's lane lights now come on before he reaches the seal, and Up Only's go off after it, so nothing switches in view.
- **Water glare:** the water is rougher, and the light in DL-08's pit sits higher and dimmer.
- **Pushing into pits:** the cart (DL-01) and the duct (DL-11) tip: front wheels over the edge, a slide, and they settle.
- **The weigh-in body:** its sheet ripples as it is dragged.
- **The couriers reveal:** it is held until he walks through the gate. Then the camera pans across the racks and a sombre cue plays.
- **The weights into the bucket:** the wide frame keeps D-17 in it.
- **Floating parcels:** the pile on the sorting floor rests on the floor.
- **EVERYONE UP:** cut back to its first appearance (DL-06) and C-106's wall in ring C.
- **The city:** gone dark. A few lamps stay, and there is more ruin and overgrowth.
- **The ending:** a real ending. He walks out of C-114 into the dark, the screen fades, then END OF CHAPTER 1 and its summary. It no longer looks like the title menu.
- **Testing:** a scene select (DL-01 to DL-11) on the title card and the pause card.
- **Judder riding a carrier up the ramp:** to profile.
- **Telemetry** (asked for alongside these notes): anonymous play data for wider playtests, see section 4.

## 4. Telemetry

The game records what testers do so we can see where they stall, die or quit, without watching each session.
- **Events:**
  - scene and checkpoint changes;
  - deaths with their cause;
  - interactions and button prompts;
  - 25-second idles;
  - curiosities;
  - puzzle signals (the weigh-in's readings, lift buzzes, cage dips, the White's warnings);
  - pauses, reloads, scene-select starts;
  - frame rate every 10 s;
  - the end, and leaving.
- **Session facts:** coarse device facts and the options. No personal data; a random id per page load.
- **Where it goes:**
  - to any endpoint given as `?telemetry=URL`;
  - always kept locally, saved from the pause card (Save play log).
- **Tools:** `tools/telemetry/collector.py` collects; `tools/telemetry/summarise.py` reports per scene.
- **Opt-out:** players can turn it off in Options, and the title card says it's on.

## Status: built

Built 20 October 2026 in `game/undelivered/`, `art/pass3`, `art/pass4`, `art/dl04`, `art/dl05`, `art/d17`,
`art/music` and `tools/telemetry`. All of sections 1 to 4 shipped as written, with these notes:
- **The cage plates** had been invisible since pass 2: the child mesh sat at the group's height again. They now show in
  his hands and on the pans.
- **Signs:** the stencil font the sign textures asked for (DejaVu Sans Condensed Bold) isn't installed, so signs had
  fallen back to a small default face. They now use Carlito Bold, and the sign textures were regenerated.
- **The judder riding the carrier:** the carriers moved after D-17 was placed, so he trailed his carrier by one frame.
  The gap changed with every frame's length, so the two jittered against each other on the ramp. He is now placed
  again after the carriers move (`syncRide`).
- **Still open:**
  - DL-11's lair still barely reads through the White's water;
  - from the DL-09 balcony, the white shell of the lobby block shows at the frame's edge.

Measured:
- **20 simulated first playthroughs** (`tools/sim/results_pass5_first_playthrough.jsonl`), all completed with no page
  errors:
  - mean 19:15 and median 19:51 of play (range 14:41 to 22:13);
  - pass 3 was 17:37;
  - 0.5 deaths a run.
- **The mechanical floor:** 7:45.
- **Shader compiles during play:** 3, at a scene-select start, as before. No new hitch sources.
