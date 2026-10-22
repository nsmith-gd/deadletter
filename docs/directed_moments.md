# Directed moments: camera and score as one

**Status:** 22 October 2026. The director's note on Version 29: "I didn't feel emotional swell in conjunction with the
camera work. You and the camera need to work in tandem together to create directed moments of wonder, sadness, and
intrigue. Pick your moments carefully when they matter for story and then really elevate them."

**Research:** `research_notes/Camera and score directed moments/` (film and games).
**Music:** `art/music/prologue_cues.py`; files in `art/music/prologue/`. Each moment's camera keyframes are also in
`prologue_music.json` under `scene_cues[].camera`.

## Why the swells missed

Music and camera were started by different triggers, so they drifted apart:

| Moment | The problem |
|---|---|
| **The city (DL-09)** | `refuge` started as he walked up to the balcony (`VISTA_X0`). The crane started at a different trigger further along (`AWE_X`). The swell's peak and the widest frame were seconds apart, and the gap depended on how fast he walked. |
| **One of many (DL-04)** | `kin` was queued behind the 36 s `racks` cue. The shot that comes round to his face as he touches his chest usually played over the tail of `racks`, with nothing of its own. |
| **The lit window (the end)** | As the camera rose to the window, the end card's lament played, which is the wrong emotion for that reveal. |
| **The marks (DL-11)** | The shot held for only 2.6 s. The true E arrived at 5.1 s, after the shot had let go. |
| **Ring C (DL-10)** | `collapse` was queued after `lastcar`, so its start depended on decode and queue timing, not on the camera. |

## The rules we are working to

From the research. The numbers are rules of thumb, to be tuned by eye and ear.

1. **Ration.**
   - The prologue gets **two full swells**: the city (wonder) and ring C (grief and horror).
   - It gets **two quiet moments**: one of many (grief) and the lit window (intrigue).
   - Everything else stays restrained.
   - The research advises at most one full swell per 10–15 minutes.
2. **Take away before you give.** Thin the music to almost nothing, or to silence, for 1.5–4 s before the move.
3. **One timeline.** The camera's keyframes are written in the cue's seconds and read from the cue's own audio clock,
   so the two cannot drift.
4. **Land the peak on the frame that tells the story,** never before it. Sound arriving early by more than about
   45 ms reads as wrong; up to about 125 ms late is tolerated. The camera should ease to a stop over the last 0.5–1 s
   before that frame.
5. **Delay the response when the player has to understand something.** Grief gets a solo instrument entering 1–2 s
   after the event, on the held shot. A physical event, such as the light coming on over the dead, gets its hit on
   the frame.
6. **Hold, then release with no second climax.**
   - Hold 4–8 s for wonder and 6–12 s for grief.
   - Hand control back while the music decays, not at the peak.
7. **No voices from about 1 s before to 3 s after a peak.** Lower the sound effects, not raise the music.

## The moments

Times are seconds from the moment's trigger, which is also the cue's start.

### 1. One of many (DL-04): grief, quiet. Cue `kin` (28 s, then heaps)

- **Trigger:** `realise`, as now. Stop `racks` (1 s fade) and the ambience at once; do not queue.

| t | Camera | Music |
|---|---|---|
| 0 | Over his shoulder along the rows (the realise shot as now). | `racks` falls away; only the pedal and a breath of choir. |
| 3.7–5.3 | Round to his face as he touches his chest (as now). | Still almost nothing. |
| 5.3–9 | **Hold close** on his face and chest. | **6.0: a solo cello enters**, a beat after the touch. |
| 9–15 | **New:** a slow pull back and up from him, until he is small and the rows run away into the dark. Ease to a stop at 15. | Strings and choir gather under the cello; a soft timpani roll. |
| **15** | **The wide over the racks.** | **The peak:** B-flat over D, held. It is moderate: about 4 dB over the build. |
| 15–21 | Hold the wide. | The violins sigh E-flat to D. |
| 21–23.5 | Ease back to the side view. | It lets go; 22.0: the music box (its E sagging). |

- **Control:** about 22.5, at SadWalk, as now.
- **Handover:** at 28 the heaps loop takes over.
- **Voices:** none from 0 to 21 s, so the racks roll call must be over or stopped.

### 2. The city (DL-09): wonder, full swell. Cue `refuge` (24 s, then order)

- **Trigger:** the awe stop at `AWE_X`. **Remove the `VISTA_X0` trigger.** Nothing plays from the tunnel to the stop.

| t | Camera | Music |
|---|---|---|
| 0–2 | He stops and turns; the camera on his shoulder, looking out into the dark (as now). | **Held breath:** air and one high violin note. |
| 2–10 | **The crane up and back** (the vista shot as now), driven by this clock, easing to a stop over the last second. | The music climbs with it: a violin line rising a step a beat over D minor, B-flat, F and C. Choir and strings gather; a timpani roll and cymbal swell from 7.4 s. |
| **10** | **The widest frame.** | **The peak:** F major, everything (strings, choir, organ, horns, piano). The loudest point is about −17 dBFS. |
| 10–16 | Hold the wide (6 s). | It holds. At 11.5 the horns, far off, play the anthem's opening: the city is the Order's. |
| 16–18.5 | Come back to him. | It lets go through B-flat to F. |
| 20–24 | Walking on. | The march creeps in for the lobby; order takes over at 24. |

- **Control:** 18.5.

### 3. Ring C (DL-10): grief and horror, full swell. Cue `ringc` (24 s, then heaps)

- **Trigger:** UP on the counterweight panel, as now. **One cue replaces `lastcar` and `collapse`; do not queue.**

| t | Camera | Music |
|---|---|---|
| 0–5.5 | Low beside him, up at the car leaving with the suitcase (car10, as now). | The anthem's close on organ and horns. **2.5: the tape runs down**, dying as the car leaves the frame. |
| 5.5–6 | He lands; hold a beat. | **Silence.** True silence from 5.5 to 9.5 s is the absence. |
| 6–9 | Rise over his shoulder to look down ring C's lane in the dark (ringc10), easing to a stop by 9.0. | Silence. |
| 9.5 | Hold; **the cold light starts to come up** over the lane. | The tannoy's chime, alone in the dark: *order above all*. Then a riser, snare and timpani climb. |
| **12** | **The light is full on the lane and its dead.** The light ramp must end exactly here. | **The collapse:** E-flat major over D, with taiko, crash and bells. The loudest point is about −12 dBFS, the biggest in the prologue. |
| 12–20 | Hold (8 s). | The anthem's opening falls in Phrygian, decaying. |
| 20–22.5 | Ease back to him. | It lets go to the cello's lament. |

- **Control:** 22.0.
- **Handover:** at 24 the heaps loop takes over, low, in ring C.

### 4. The lit window (the end): intrigue and hope, quiet. Cue `window` (20 s)

- **Trigger:** the look phase on the landing (`e.pt = 0`). This replaces `end` here; `prologue_cue_end` plays on the
  end card after the fade.

| t | Camera | Music |
|---|---|---|
| 0–1.5 | He stops and looks up; the camera is still, low behind him. | Near silence. |
| 1.5–6.5 | Rise with his look up the well (5 s; the window shot as now, retimed). | The music box climbs one note a beat (D, F, G, A, C) over a thin high string and a soft choir. |
| **6.5** | **The one lit window, held,** easing to a stop over the last second. | **F with a major seventh,** and a high violin on the **true E**: someone up there turned the lights on. It does not resolve. |
| 6.5–11.5 | Hold (5 s). | The music box sounds a few irregular notes, like a signal. |
| 11.5–13.5 | Come back down to him. | It thins to an open fifth. |
| 13.6 | He checks his label (move it from 10.5 to 13.6). | **13.8: the parcel's notes, with the true E.** |
| then | The stair, the fade. | Then the end card's cue. |

### Smaller, synced only

- **The marks (DL-11):** raise `MARKS_HOLD` from 2.6 to 6.0 s. `childP` already starts on the shot. The music box now
  plays the parcel's notes at 1.2 s, with the **true E at 2.3 s**, while the marks are held.
- **Unchanged and restrained:** wake, hall, threshold, racks, dead, latch, child and end. They are not "moments" and
  should not swell.

## How the game should run a moment

- **`Music.moment(name)`:**
  - Cancel any queue, fade the current cue and the ambience out over 1 s, and start the cue at
    `startAt = ctx.currentTime + 0.05`.
  - Decode the moment cues ahead of time, on entering their scene, so the start has no latency.
  - If the buffer is not ready, the moment starts when the cue really starts.
- **`Music.momentTime()`:** returns `ctx.currentTime - startAt - (ctx.outputLatency || ctx.baseLatency || 0)`, clamped
  at 0. The shot reads this, not `game.clock` or `e.pt`, so frame-rate dips and decode delays cannot pull the camera
  off the music. If music is off, fall back to the game clock from the trigger.
- **Keyframes:** build each moment's shot from the keyframes above, smoothstep within each segment. While it runs,
  raise the follow rate (`ease` about 4) so the camera lags by less than about 0.2 s.
- **Control and voices:** keep control locked until the `control` time. Suppress voices and tannoys inside the
  moment.
- **Handover:** at the cue's `handover`, the named loop restarts from `loop_start`, as for every scene cue.
