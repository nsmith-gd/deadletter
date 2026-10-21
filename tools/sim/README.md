# Simulated first playthroughs

A simulated player plays the whole of Chapter 1 (DL-01 to DL-09) inside the page and records the time of each scene.
Scene times come from the game's own scene names (`window.__dl01.scene()`), so they follow the game when a scene's
bounds move.

- **`bot.js`:** the simulated player. It drives the game's own input, one call per 60 Hz game step, through the
  test-only `window.__sim` hook in `game/undelivered/index.html`. That hook runs several steps per frame and renders
  only now and then, so a playthrough takes about a minute.
  - Every action is a real one in the game: walking, jumping, Use, carrying, pushing, riding a carrier into the pile.
  - Curious players pick up the undelivered letters and post them; the rest walk past.
  - A player model adds the time a person spends looking, reading, thinking and trying the wrong thing first.
  - Each run draws its own player (skill and curiosity, from 0 to 1) from its seed.
  - The think times are calibrated guesses from the first live playtest, not measurements. Check them against real
    playtest times (the end card shows the total).
- **`sim.mjs`:** runs the playthroughs in headless Chromium.
  - Usage: `node sim.mjs <first seed> <count> <out.jsonl> [mechanical]`.
  - `PROGRESS=1` prints the clock, place and last event every 30 s; `TRACE=<label>` writes every walk step whose
    label contains it to `<out.jsonl>.trace`. A page error stops the run and is reported.
  - `mechanical` turns the player model off, which gives the shortest possible time.
  - It needs `playwright-core` and a local copy of `three` in `node_modules/`.
  - It needs the game served at `http://127.0.0.1:8765` (or set `GAME`).
- **`summarise.py`:** turns the results into per-scene mean, median, min and max times.
  - Usage: `python3 summarise.py results.jsonl`.
- **`results_first_playthrough.jsonl`:** the five-scene build's batch of 20 runs (seeds 201 to 220).
- **`results_chapter1_first_playthrough.jsonl`:** the nine-scene Chapter 1, 20 runs (seeds 101 to 120), all completed.
  Mean 13:42 and median 13:34 of play (range 10:13 to 16:52), plus the 20 s opening. Half the players rode a carrier
  into the chute in DL-05.
- **`results_chapter1_mechanical.jsonl`:** the nine-scene floor with the player model off: 5:28 of play (it was 3:54
  for the five-scene build).
- **Calibration:** the five-scene build's simulated mean was 9:13, against the director's own run of 5:43. If that
  ratio holds, an experienced player would take about 8:30 here. Real first-time playtests are still needed.
- **`results_pass2_first_playthrough.jsonl`:** Chapter 1 after pass 2 (curiosities, the White, hazards, the if-then sequences), 20 runs
  (seeds 101 to 120), all completed. Mean 14:55 and median 15:08 of play (range 11:27 to 19:09), plus the 20 s opening.
  The simulated players died 1.2 times a run on average (at most 4) and found 6 of the 12 curiosities on average.
- **`results_pass2_mechanical.jsonl`:** the pass 2 floor with the player model off: 6:14 of play.
- **`results_pass3_first_playthrough.jsonl`:** the eleven-scene Chapter 1 after pass 3, 20 runs, all completed. Mean
  17:37 and median 17:47 of play (range 13:01 to 20:51), plus the 20 s opening.
- **`results_pass5_first_playthrough.jsonl`:** Chapter 1 after pass 5 (the weigh-in, the reveal at the gate, the tipping
  cart and duct, the ending), 20 runs (seeds 201 to 220), all completed with no page errors. Mean 19:15 and median 19:51
  of play (range 14:41 to 22:13). Most of the 1:38 over pass 3 is DL-05's weigh-in (+0:24), DL-06 (+0:20) and
  DL-08 (+0:14). Deaths 0.5 a run (at most 2); curiosities 5.8 a run.
  - The opening card is timed in real seconds, so the sim's sped-up clock inflates its "opening" row (about 1:30).
    For a player the card is 12.5 s or less, then the 20 s wake.
  - `QUERY` appends a query string to the game's URL, for example `QUERY='?telemetry=http://127.0.0.1:8787/events'`
    to send the runs' telemetry to a local collector.
- **`results_pass5_mechanical.jsonl`:** the pass 5 floor with the player model off: 7:45 of play.
- **`results_pass8_mechanical.jsonl`:** the prologue after pass 8 (the wake's label beat and dispatch, the progressive
  weigh-in, the desk letting go), player model off: 8:08 of play, end to end.
- **`results_pass8_attendance_mechanical.jsonl`** and **`results_pass8_attendance_first_playthrough.jsonl`:** Chapter 1
  with the reworked DL-14 (the pole starts in A's wheel): 2:39 mechanical; three first-time runs at 4:27 to 4:58.

## The interaction-overlap audit

`audit_near.mjs` (run it like `sim.mjs`, from a folder with playwright-core and three, the game served on :8765) loads
every checkpoint in turn and sweeps D-17 along the stretch to the next one, on the floor and on whatever he could
stand on, asking each category of interaction alone. Any spot where two answer Use is a priority clash and is listed;
the script exits non-zero if there are any. Run it after moving anything he can use.
- **`results_pass9_attendance_mechanical.jsonl`** and **`results_pass9_attendance_first_playthrough.jsonl`:** the whole
  of Chapter 1 (DL-12 to DL-17): 4:45 mechanical; three first-time runs at 6:52 to 7:21, of which DL-15 to DL-17 take
  2:28 to 2:48. `CHAPTER=att2` starts at DL-15.
