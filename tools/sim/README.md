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
- **`results_pass10_mechanical.jsonl`** and **`results_pass10_first_playthrough.jsonl`:** the prologue after pass 10
  (glints and prompts, two-sided pushables, the cot, weight lamps): 7:56 mechanical; three first-time runs at 15:02 to
  16:29 of play. The overlap audit is clean, including the twin pushables and the cot (the cart's grip reaches less far
  back to leave it room). `CONTINUE=1` (prologue end into chapter one through the end card's button) passes.
- **`results_rev03_attendance_mechanical.jsonl`** and **`results_rev03_attendance_first_playthrough.jsonl`:** chapter 1 after the
  director's plan revision 0.3 (rail docks only at Abel's and Orme's places, the stair door out of DL-17): 4:40
  mechanical, 6:57 first-time. The bot now leaves DL-17 by the stair. The overlap audit is clean.
- **`results_moments_mechanical.jsonl`** and **`results_moments_first_playthrough.jsonl`:** the prologue with the four
  directed moments (kin, the city, ring C, the lit window) held on their cues: 8:41 mechanical (7:56 before; the holds
  add about 37 s), and one first-time run. Under the sim a moment runs on the game's clock.
- **`results_expansion_attendance_mechanical.jsonl`** and **`results_expansion_attendance_first_playthrough.jsonl`:**
  chapter 1 with the expansion (DL-14a, DL-14b, DL-16a, DL-17's rig) and the design review's trims, on the new sets:
  6:40 mechanical; three first-time runs at 9:45 to 11:15 (about 7:00 before). The overlap audit is clean.

## Golden traces for the Unity port (`record_trace.mjs`)

`record_trace.mjs` runs the simulated player and writes what the game did at every 60 Hz step, so Core can replay the
same inputs and be compared step by step (`unity/core-tests/Dl01TraceTests.cs`).
- Usage: `node record_trace.mjs <seed> <out.jsonl.gz> [mechanical]`, from a folder with `playwright-core` and `three`
  in `node_modules/`, the game served on :8765 (or `GAME`). `CHROME` = the Chromium binary, `BOT` = bot.js (default:
  next to the script), `RNG_SEED` = the page's `Math.random` seed (default 1), `PROGRESS=1` prints progress,
  `BOT_OPTS` = JSON merged into the bot's options (recorded in the header as `botOpts`), `UNTIL` = game-clock seconds
  after which the recording stops (the end line says `"stopped": true`; the header has `until`).
- **Determinism.** Before the page's scripts, `Math.random` becomes the prototype's own LCG (`s = (s·16807 + 11) mod
  2147483647`, as Core's `SimRng.Lcg`). The recorder's first step reseeds it, puts `setTimeout` and
  `AudioContext.currentTime` on game time (1/60 s a step), sets `game.clock = 0` and presses Begin, so the real-time
  title screen never reaches the trace. Two recordings of the same seed are byte-identical. (DL-01's own state draws
  no random numbers; later scenes do: crates, carrier payloads, the White.)
- **`unity/core-tests/Traces/prologue_mech_seed1.jsonl.gz`:** the whole prologue, mechanical, seed 1: 33,207 steps
  (play from step 1768, `room` at 4082, DL-03 from 5228 to 6278, the end card at 553 s).
- **`unity/core-tests/Traces/dl02_press_death_seed1.jsonl.gz`:** the same run with `BOT_OPTS='{"pressMistake":true}'`
  and `UNTIL=100`: identical to the prologue's up to DL-02's press, where the bot walks in on the slam (bot.js
  `passPress`), is crushed (#4106), respawns at `room` (#4185) and goes on into DL-03; 71 KB (`Dl02TraceTests`).
- **Format** (`deadletter-trace/1`): gzip, one JSON object per line. Line 1 is a header (`format`, `seed`, `mode`,
  `rngSeed`, `rng`, `step`, `round`, `delta: true`); the last line is `{"end": true, steps, error, marks, events}`.
  Every other line is step `i` (0-based, from Begin) and holds **only the fields that changed** since the line before;
  a reader carries the rest forward. Numbers are rounded to 1e-6, except `clk`, which is exact (the quirk timers
  compare `game.clock` differences, so a replay starts from the recorded clock bit for bit).
  - Input the step consumed (after the bot set it, before `step()`): `L`, `R` (keys held), `JP`/`JH` (jump pressed,
    held), `UP`/`UH` (use pressed, held), `SH` (`input.shift`, the walk modifier), `AX` (`input.axis`, 0 without a pad).
  - D-17 after the step: `clk`, `x`, `y`, `z` (three.js: − into the set), `vx`, `vy`, `yaw`, `f` (facing), `g`
    (grounded), `c` (crouched), `m` (mode), `a` (`kind:phase` of `game.act`, `quirk:<clip>` for quirks, null), `h`
    (`game.hold`, `push:<key>` while pushing), `mt` (mantling), `tr` (transit stage, −1), `r` (region), `cp`
    (checkpoint), `fr` (`game.frame`), `clip` (the clip playing), `sc` (`sceneName()`).
  - DL-01: `rel` (released), `sh` (shutter angle), `lv` (latch lever angle), `wy` (counterweight y), `door`
    (`doorOpen`), `wh` (wheel angle), `cx`/`cs`/`cd`/`cl` (the cart's x, state, drop, lip), `nr` (`nextRelay`).
  - DL-02, only while `r` is 2 and x < `SH.x1` + 1 (so its exit step too; no other step's line changes): `pf` (the
    press's face, from its model), `bx`/`bb`/`bs` (the box's x, base and state), `tl` (`letterState.tube`), `dn`
    (`game.deaths`), `ra` (`game.respawnAt`, 0 = none). Adding them left every line before the passage's stage 2
    (steps 0–3998) byte-identical and every earlier field of every step unchanged.
  - DL-03 (`unity/core-tests/Dl03TraceTests.cs`): `tx` (the trolley's x), `ws`/`wx`/`wo` (the sort weight's state,
    `x` and deck offset), `ld` (`game.load`, the plate with him), `nd` (the gauge's needle), `gy`/`gv` (the gate's
    height and fall speed). Added after DL-01's: every DL-01 field is unchanged at every step (only step 0's line gains
    the new keys, at their reset values).
  - DL-04 (`unity/core-tests/Dl04TraceTests.cs`), only while `r` is 2 and 30.6 ≤ x < `RATION5.x0` + 1 (so its exit
    step too; `null` before, carried forward after): `kx4`/`ks4` (the fallen courier's x and state: free, drawn,
    cradle, seated), `ka4` (the cradle's arms, `rotation.x`), `bd4` (`ch1.bayDoor`, 0..1), `bw4` (what the bay wants:
    him on the plate or the courier seated, read back from the plate's 1 cm dip). Adding them left every line outside
    DL-04 byte-identical and every earlier field of every step unchanged.
  - DL-05 (`unity/core-tests/Dl05TraceTests.cs`), only while `r` is 2 and x ≥ `RATION5.x0` (47.9), and on the step he
    leaves (so steps 9868–12073 here): `d5x`/`d5s` (the drum's x and state), `b5x`/`b5s` (the body's), `w5` (the
    weigh-in's W, recomputed as `updateCh1` weighs it, L4890–L4892), `w5r` (its reading), `n5` (the needle), `p5` (the
    plate's dip), `t5` (the hatch's twitch lift, L4920), `h5` (`rh.h`, the hatch's height), `f5` (the SERVED flag),
    `s5` (served). Every earlier field of every step is unchanged. Note: `setTimeout`s run at the start of the
    recorder's per-step call, before it writes the previous step's line, so a timeout's effects (DL-05's pat) show on
    the step before the one they first act in.
  - DL-06 (`unity/core-tests/Dl06TraceTests.cs`), only while `sceneName()` is DL-06 and on the step he leaves it (so
    steps 12073–14016 here): `sp6`/`st6` (the scanner's phase and `scan.t`), `bl6` (`belt.running`), `rt6`
    (`game.route`), `sl6`/`pl6` (the stop and points levers' angles as the levers set them: `leverHold`'s angle in an
    act, else the rest angle, before the view's easing, L2833–L2834), `rd6` (the id of the carrier he rides, null),
    `cr6` (the carriers as one JSON string: `[id, state, route, x, y, s, wait, t, ridden, tip, [[size, z, yaw], ...]]`
    each, from `root.position`, `pivot.rotation.z` and the payload's meshes). Every line is unchanged apart from these
    keys (checked line by line against the previous recording).
  - A later scene's port adds its own fields the same way (a new format version if a field changes meaning).
- **Chapter 1 (`CHAPTER=att`, U-22):** `CHAPTER=att node record_trace.mjs 1 attendance_mech_seed1.jsonl.gz mechanical`
  records Chapter 1 Attendance from `school`, as `sim.mjs` plays it. The school's set is loaded before the bot starts,
  so the first step's `startAt('school')` runs synchronously and the run stays deterministic (two recordings are
  byte-identical); the header has `chapter` and `start`. **In region 6 the prologue's DL-06 carrier line is held off**
  (`game.belt.running = false`, no carriers): `resetWorld` starts its belt at every checkpoint past `scanned`, and each
  chute tip startles him anywhere past x 67.8 on the floor (L2734 has no region test), every 6 s, drawing
  `Math.random`. That is a leak of the prologue into the school, not chapter 1, so it stays out of the trace.
  - **`unity/core-tests/Traces/attendance_mech_seed1.jsonl.gz`:** the whole of Chapter 1, mechanical, seed 1: 20,842
    steps (DL-13 from #1313, DL-14 from #3042, the duct at #7886, DL-14a from #8265; the end at 347 s).
  - Its fields, only while `r` is 6 (so no prologue line changes), named with the scene's number:
    - The whole chapter: `aw` (`game.act.what` of an `att` act, as `beginAtt` names it: `coat`, `hang`, `pawl`, `crank`,
      `duct`, …; null otherwise).
    - DL-12: `c12x`/`c12b`/`c12s` (the coat's x, base, state), `f12x`/`f12v` (the stand-in figure), `g12y`/`g12v`
      (the gate's height and fall speed), `p12` (someone on the strip), `pc12` (`presentCount`).
    - DL-13: `f13x`/`f13v` (the second figure), `l13` (the lesson on), `t13` (its clock), `k13` (braked), `s13` (the
      three steps, comma-separated), `tr13` (the tree).
    - DL-14: `ba14`/`bb14` (the blinds), `ta14`/`tb14` (their targets), `w14` (winds), `j14` (jammed), `px14`/`pb14`/`ps14`
      (the pole's x, base, state), `pe14`/`pd14` (the peel, peeled), `rt14` (the chain rattling on the pole), `du14`
      (the duct taken).
    - DL-14a: `nt14a`/`nk14a` (the night-light's clock, braked), `w1a`/`w2a`, `t1a`/`t2a` (the blinds and their
      targets), `wn14a` (winds), `do14a`/`op14a` (the door, open), `gx14a`/`gb14a`/`gs14a` and `bx14a`/`bb14a`/`bs14a`
      (the gown and the bag: x, base, state).
    - DL-14b: `tx14b`/`td14b`/`tm14b`/`tt14b` (the escort trolley's x, direction, mode and its mode clock),
      `fx14b`/`fs14b`/`fo14b`/`fk14b` (the figure in the bay: x, state, out, kept), `hd14b` (hiding).
    - DL-15: `ax15`/`ab15`/`as15`/`al15` and `bx15`/`bb15`/`bs15`/`bl15` (figures A and B: x, base, state, lean),
      `li15`/`lv15` (the pupil lift's height and speed), `lm15` (the seat lamps, comma-separated), `se15` (seated),
      `di15` (dismissed), `do15` (the class door).
    - DL-16: `br16` (the bridge), `la16` (latched), `he16` (the lever held), `sn16` (figures stored), `cw16` (the
      rack's counterweight).
    - DL-16a: `sx16a`/`ss16a` (the stool), `h16a`/`m16a`/`mt16a` (the dumbwaiter's height, mode and clock), `t1_16a`,
      `t2_16a`, `bk16a` (the tins and the books, each "x,base,state").
    - DL-17: `ty17` (the tray, "x,base,state"), `dr17` (the drawer), `rd17` (read), `ky17` (the T-key), `sl17` (the
      sluices), `tk17`/`ru17` (the tank and its run), `be17` (the beds), `lt17`/`ld17` (the float latch, latched),
      `do17` (the stair door), `en17` (the chapter ended).
  - Adding DL-14a's to DL-17's fields left every earlier field of every line unchanged (checked line by line).
