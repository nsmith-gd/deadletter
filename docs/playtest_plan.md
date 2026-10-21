# Playtest plan: first-time players

**Why:** the director's note, 21 October 2026: "Strong start but still a bit short, needs a play test with someone who
doesn't know how the game works." The simulated players have done what they can. They know every solution and only
pretend to look; the next real information comes from people.

## Who
- **Five people who have never seen the game.** One at a time; five usually find most of the problems.
- **A mix:**
  - two who rarely play games;
  - two who play puzzle or story games (Limbo, Inside, Little Nightmares);
  - one who plays mostly fast games.
- **Not developers,** and not anyone who has heard the story.

## Setup (per session, about 45 minutes)
1. Share the artifact with them (its Share menu), or host the build anywhere static. If the game is hosted, add
   `?telemetry=https://<your collector>/events` to its link, so their run lands in `tools/telemetry/collector.py`.
2. **Desktop with headphones** for at least three of the five; that's what the game is tuned for. A gamepad if they want
   one.
3. Before they start, tell them only: "It's a short game about a delivery robot. Play however you like. Think out
   loud if you can. I won't help unless you're completely stuck for a few minutes."
4. They play the prologue from the start, then press **Continue to chapter one** on the end card.
5. **If there's no telemetry endpoint,** ask them, at the end, to open the pause menu and press **Save play log**, and
   to send you the file.

## Watch for (write the time each happens)

| Moment | What to note |
|---|---|
| The opening card and the wake | Did they read the card? Did they understand they carry a parcel for someone? (Ask after.) |
| Each puzzle | First thing they tried. How long until the aha. Any time they said "what?" or went quiet for more than 30 s. |
| DL-03, the gate | Did they crawl under a half-open gate? |
| DL-05, the weigh-in | Did they notice the hatch jerk when the needle passed PERSON? Did they think of the body before the drum? |
| DL-06, the carriers | Did they ride one? Did they find the secret room? |
| DL-09, the cage and the hopscotch | Did they take the hopscotch? Did they hear the music box and find the den? |
| The voices | Did they wind any players? Did they stop to listen, or walk away while one played? |
| The ending | Did they see the window? Ask: "Who do you think turned the lights on?" |
| Chapter 1 | DL-12: how long before they thought of the figure as a pupil? DL-13: did they read the dial, or brake by luck? DL-14: did they think of the pole as a jam? |
| Anywhere | Deaths. Where they got lost. Where they were bored (fidgeting, skipping). |

## Questions afterwards (in this order; don't lead)
1. "Tell me what happened, in your own words." (Do they tell the story? Which parts?)
2. "Who was D-17 delivering to? What was in the parcel?"
3. "What do you think happened to all the people?"
4. "Was there any moment you felt stuck and stupid, rather than stuck and curious?"
5. "Which moment will you remember tomorrow?"
6. "Did it feel too long, too short, or right?"

## Reading the results
- `python tools/telemetry/summarise.py <logs>` gives per-scene times, deaths, idles, prompts shown and quits.
- Compare against the simulated first-time players: prologue 19:15, Chapter 1 about 3:30 to 4:00. If real players
  run much longer, that's the simulation's optimism. If shorter, the puzzles are too easy, and the director's note
  stands.
- **Fix first:**
  - anywhere two or more people were stuck and stupid;
  - any story beat three or more people missed;
  - any scene two or more people called boring.

## Length
The chapters planned in `docs/roadmap.md` take the game past two hours. Each new chapter should be measured the same
way before the next is built.

## Results

| Date | Player | What | Time | Notes |
|---|---|---|---|---|
| 21 October 2026 | First-time player, rarely plays this kind of game | Prologue, cold | 26:47 | Above the roadmap's 15–20 min target and the simulated first-time players (19:15 in pass 5), which is the direction we wanted: the simulation is optimistic, and real first-time play runs longer. |

### After the first cold playtest (pass 10)

Her notes and what we saw are answered in `docs/prologue_pass10_plan.md`. In the next cold playtest also watch for:
whether the player uses the cot or the dispatch board in DL-01 (depth learned early), whether they notice the E on
far-back objects, whether they pull things from the "wrong" side and carry on, whether the weight lamps are read, and
whether either of the first two secret rooms is found. Ask afterwards whether anything was too dark (and whether they
found the brightness setting).
