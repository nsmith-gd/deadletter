# Prologue pass 10: teach it clearly

Status: built (pass 10). Source: the first cold playtest of the prologue (26:47, a player who rarely plays this kind
of game), her notes, and what the director saw while she played.

## What the playtest showed

| Seen | Why it happened | Pass 10 answer |
| --- | --- | --- |
| The game "crashed" after the prologue | Continuing to chapter one loads 19 MB with no feedback on the end card, then holds the whole depot and the school in memory at once. The sim never crashes, so this is either a slow load that looked frozen or a real out-of-memory tab crash on her machine | A loading card on Continue; a loader that decodes straight into one buffer (no 44 MB string copies); an autosave of the last checkpoint with **Continue** on the title card; a "the picture stopped" card if the graphics context is lost, with a reload that resumes |
| Exploring early did nothing, so she stopped exploring | The first secret is at DL-06, about ten minutes in. Early curiosities are mostly on the lane | Early depth: the dispatch board takes him a step back into the set; a new curiosity at the back of the depot floor (the night-shift cot) teaches that the background is reachable. The first two secret rooms spill light, glint, and draw his head the first time he passes |
| E works in depth, but nothing said so | Use on a far-back object looks like nothing is there | Every interaction near him glints where it actually is (in depth), and when Use would do something the E prompt sits on the object, not on him |
| Levers and switches were missed | Unlit | The nearest usable things get a real warm lamp from the light pool (two at a time), plus the glint |
| She pushed a body she had to pull, and decided the solution was wrong | Each pushable had one working side | The courier, the drum, the body and chapter one's figures can be taken from either side. Push or pull, both move it |
| "I added weight and nothing told me" | Feedback was a stalled gate or a needle far off | Weight lamps (amber pips, green when enough) beside the DL-06 bucket gate, the DL-09 counterweight tray and the DL-10 car; each weight lights one with a tick; not enough flashes the unlit ones with a buzz |
| The lift dial "looked like it wanted lighter" | The face put "too light" on the cage's side, and the needle leaned toward the cage like a tipped scale | Both balance gauges get a new face: the start zone says ADD WEIGHT with a downward arrow and a weight; the top says OK in green |
| Read the letters she found? | The letters went straight into the slots | Picking a letter up shows it close (front and back, a line of transcription); a Letters list on the pause card keeps every one he has scanned |
| Music swelled at the city reveal | The refuge cue peaks about 7 dB over the hall cues | A gentle limiter on the music bus; the refuge and kin cues brought down |
| Dark, hard to read | Her screen is darker than ours | A brightness setting on the title and pause cards (and the interactables are now lit) |
| The eel and the letter were "buggy" | C-110's letter slid onto the duct over the White's water, right where the White had just been called by the splash; stopping to pick it up was a death | The letter flutters past the dip to the far kerb, out of the White's reach |
| Depth wasn't clear early | (see above) | The dispatch board and the cot, both in DL-01 |

## Systemic changes

1. **Glints.** Four times a second the game sweeps 3 m either side of him, asking what Use would do at each step
   (the overlap audit's sweep). Each answer gets an anchor (the curio, the lever, the far end of the thing he would
   grab) and a soft warm glint there, brighter as he nears. The one Use would do now is brightest, and carries the E
   (on touch, USE). Option: "Light up things I can use" (on by default).
2. **Lamps.** Two pool lights follow the nearest usable things, so levers and switches are lit as well as glinting.
3. **Either side.** Twin pushables share the original's state and limits; when several pushables answer, the nearest
   stand point wins. Pulling into a wall stops at the wall.
4. **Weight lamps.** A small brass plate of round lamps beside each weighing device: amber unlit, lit one per weight,
   green when enough.
5. **Resume.** Each checkpoint is saved locally; the title card offers Continue from it.

## Per scene

- **DL-01 The Wake.** The dispatch board: he steps back to it (z -0.55). The cot at the back of the depot floor
  (x 4.8, z -2.4): a curiosity that takes him deep into the set, lit and glinting from the step.
- **DL-02 The Sorting Hall.** The courier: either side. The tube letter, read close.
- **DL-05 The Ration Hall.** The drum and the body: either side.
- **DL-06 Return to Sender.** The weight lamps at the gate. The reader's panel spills light; he looks at it the first
  time he passes.
- **DL-08 The Handbrake.** The refuge cue brought down.
- **DL-09 The Slipping Cage.** The new gauge face, the tray's weight lamps. The den's vent spills light; he looks.
- **DL-10 Up Only.** The new gauge face; the car's weight lamp; UP with an empty car buzzes and flashes it.
- **DL-11.** C-110's letter lands on the far kerb.

## Measures

- The sims (first-time and mechanical) and the overlap audit must stay clean.
- Glint sweep cost under 0.5 ms a frame on the sim's machine.
- Next playtest: watch for early depth (does she use the cot or the board), the pull, the weight lamps, and whether
  the E on far objects is noticed.
