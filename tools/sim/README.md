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
- **`results_first_playthrough.jsonl`:** the first batch of 20 runs (seeds 201 to 220).
