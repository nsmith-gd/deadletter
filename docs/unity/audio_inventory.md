# Audio inventory for the Unity port

**Status:** 26 October 2026, issue #20 (U-16a). Issue #13 imports from this file.

## What this covers

Every sound in the web build (`game/undelivered/index.html`), with where it comes from and what Unity should do with
it.

- **Renders** are in `art/sfx/out/`, made by `tools/audio_render/` (see its README for how to re-run and how they were
  checked). They are 48 kHz 16-bit WAV, made from the game's own synth code run offline, so they sound exactly the
  same.
- **File names** follow `<category>_<event>[_variant].wav`. The categories are:
  - `d17`: his body and voice;
  - `mech`: machines and props;
  - `elec`: electrical;
  - `env`: water and the building;
  - `curio`: curiosities;
  - `death`: deaths;
  - `loop`: continuous layers in `Sound`;
  - `amb`: positional emitters;
  - `voice`: the voice chain;
  - `ir`: reverb impulses.
- **Line numbers** are index.html's as of commit `7b3c123` (unchanged by this work). `node tools/audio_render/callsites.mjs` regenerates the
  call-site list.

## Conventions

- **Gain.** Every file holds the level the game makes before its master gain. In the web build the routing is:
  - `Sound` → master (0.8);
  - `Ambience` → bus (0.9) → master;
  - `Voice` → bus (1) → master;
  - `Music` → bus → limiter → master.

  In Unity, use one mixer group per bus, set to those gains:
  - SFX 0.8 (−1.94 dB);
  - Ambience 0.9 × 0.8;
  - Voice 0.8;
  - Music 0.8, after its compressor.

  The **Gain** column gives the per-call volume to set on the AudioSource. The "peak" figure is the file's own level,
  for reference.
- **Dry and wet.** Every `Sound` one-shot sends to the **depot reverb**: a 2.4 s convolver, return gain 0.32,
  impulse in `ir/ir_depot_2400ms.wav`.
  - The plain file is dry.
  - `_wet` is dry plus the return, as heard in the browser.
  - Where no `_wet` exists, the return sits under −60 dBFS and the dry file is all you hear. The send levels are listed
    so a Unity send to a convolution reverb can rebuild it instead.
- **Takes.** `_v1…_vN` are takes of a sound that is randomized in code; pick one at random each time it plays. Only
  `_v1` has a `_wet` file.
- **Space.** No sound in the web build is panned: every source is mono to the centre, or a stereo reverb.
  - "2D" means not positional.
  - "2D, distance-scaled" means the caller sets the volume from his x-distance, and the formula is given.
  - "Positional" (emitters and voices) means a gain of `level × k²` (emitters) or `level × k` (voices), where
    k = max(0, 1 − |x − source x| / reach). In Unity, use a 3D source with a custom rolloff (k² or k to zero at
    `reach`). Panning can stay off to match the web build, or be turned on as a design choice.
- **Visual equivalent.** `docs/audio_audit.md` places the emitters, voices and interactables per scene. For the
  `Sound` one-shots, which it only counts, the visual is what the call site shows on screen when the sound fires.
- **Scene numbers** are the current DL-01 to DL-17 from `game/undelivered/README.md`. The code's module names use older
  numbers: `updateDL02` is DL-03 and DL-04, `updateDL03` is DL-06 and DL-07, `updateDL04` is DL-08 and DL-09, and
  `updateDL05` is DL-11. The comments in the chapter-one rework and the hazards use pre-pass-3 numbers, where their
  DL-06 to DL-09 are today's DL-07, DL-08, DL-09 and DL-11.
- **Opening frames** are at 24 fps (`FPS`, line 268): frame f is at f / 24 s into the opening.

## Sound: one-shots (index.html 559–774)

These are built from `tone(freq, dur, type, peak, rev, slideTo)` (589–594) and
`noise(dur, freq, q, peak, filterType, rev, attack)` (595–600):

- both shape their gain with `env()` (588): an exponential ramp from 0.0001 to `peak` over `attack` (4 ms for a tone),
  then an exponential ramp back to 0.0001 over `dur`;
- `out()` (584–587) sends the result to the master at 1 and to the reverb at `rev`;
- "Rev" in the table is the largest send among a sound's parts.

| Sound | Source | Trigger (scene: event, line) | Type | Gain (volume; file peak) | Space | Visual equivalent | Output |
|---|---|---|---|---|---|---|---|
| tick | `tick` 606 | DL-01 opening, frames 18, 25, 34 (1582). DL-05 weigh-in dial passing each 20° detent (4906). DL-07 wound clock, once a second while near it, upper deck (6795) | one-shot | 1; −30.5 dBFS. Rev 0.2 | 2D | dial needle stepping; clock hand | `mech_tick` |
| relay | `relay(i, strength)` 607 | DL-01 opening, i = 0, 1, 2 at frames 120, 132, 144 (×0.5), 168, 180, 192 and 336, 348, 360 (1583–1589). **Depot relay pulse**: every 6 s (144 frames) in play, i = 0, 1, 2 at 0, 0.5, 1.0 s, strength k·max(0.25, 0.8 − \|x − 2\|/8), where k fades to 0 in DL-08 past OFF3 + 57 (8515). DL-11 terminal, ×0.6 (3622) | one-shot | strength (0.25–1); −21 dBFS. Rev 0.7 | 2D, distance-scaled (pulse) | the three relay lamps flicking on | `mech_relay_0/1/2` (+`_wet`); the whole pulse at strength 1: `mech_relay_pulse` (+`_wet`) |
| spark | `spark` 608 | DL-01 opening, frames 150, 153, 196 (1584, 1586). Water flinch: he touches live water, with sparks (4513) | one-shot, random | 1; −21 to −24 dBFS. Rev 0.5 | 2D | spark burst | `mech_spark_v1..3` (+`_v1_wet`) |
| answer | `answer(i)` 609 | DL-01 opening, frames 172, 184, 196 (1585–1586). DL-06 scanner's three answer lamps (2797). DL-11 terminal, 120 ms after each relay (3622) | one-shot | 1; −32 dBFS. Rev 0.3 | 2D | answer lamp lights | `mech_answer_0/1/2` |
| servo | `servo(dur, f0, f1, peak)` 610 | One file per argument set (name `mech_servo_<ms>_<f0>_<f1>`, peak in the file):<br>• 120_900_1300: opening frame 217, he wakes (1586)<br>• 400_400_1600: frame 225<br>• 220_300_520: frame 240<br>• 220_320_560: frame 258<br>• 240_340_620: frame 276<br>• 2000_180_420: frame 300, the long rise (1588)<br>• 120_500_900: frame 360 (1589)<br>• 200_500_900: DL-01 cord lamp tug (1848)<br>• 150_400_700: lever pull, DL-06 (2913) and DL-08 (3303)<br>• 350_900_1500: letter close-up scan (3951)<br>• 500_260_520: DL-04 bay cradle draws the courier in (4790)<br>• 600_300_700: the cradle seats it (4805)<br>• 250_500_820: reach up, DL-12 coat to the peg (5307) and DL-14a gown hem (6072)<br>• 300_300_500: the DL-14→15 duct, turning along it (5638)<br>• 200_400_520: DL-17 spindle without its key (6212)<br>• 200_120_160: school relay box pump while the tank refills, random about 3/s within 6 m (6324)<br>• 300_300_420: DL-14b escort trolley turns (6378)<br>• 220_700_1250: weight lamps, all pips lit (6870) | one-shot | 1; −28 to −38 dBFS. Rev 0.3 | 2D | his head and arms moving; cradle arms; trolley turning | 18 `mech_servo_*` files (wet under −60) |
| click | `click` 611 | Opening frame 312. Mantle, 1.4 s in (1911). DL-11 back-door latch (3666). DL-10 UP button (4583). DL-05 plate reads a person (4899). DL-16a call and bell pushes (6146, 6170). School relay boxes switching (6323) | one-shot | 1; −17.4 dBFS. Rev 0.5 | 2D | button or latch | `mech_click` |
| grit | `grit` 612 | DL-01 opening frame 350: grit shaken loose from the shutter (1589) | one-shot, random (14 ticks over 0.7 s) | 1; −22 to −26 dBFS. Rev 0.4 | 2D | falling grit particles | `mech_grit_v1..2` |
| chirp | `chirp` 613 | Opening frame 414. DL-06 scanner reads him, and he perks up at the label (2800, 2811). DL-09 hopscotch (3406). DL-11 forwarding stamp (3624). Letter posted, 250 ms after the knock (4486) | one-shot | 1; −24.5 dBFS. Rev 0.4 | 2D | D-17's pleased two-note chirp | `d17_chirp` (+`_wet`) |
| worried | `worried` 614 | DL-01 cord flinch (1875) and stuck at the trench (4520). DL-03 nowhere to set down (2268), and a sigh (2308). DL-07 tipped into the chute (2981). DL-08 teeter (3281). DL-09 hopscotch (3406). Water flinch (4513). DL-17 tank not full (6203). Knocked back by the White (7201) | one-shot | 1; −26 dBFS. Rev 0.4 | 2D | his flinch or startle | `d17_worried` |
| tap | `tap` 615 | Contact taps. Opening frames 392, 400. Grab (1852). Hopscotch (3406). DL-11 toy pat (3627). Body grab (4464, 4466). Letter pick-up (4473). Push detent (4720). DL-02 tube letter, 200 ms (4772). DL-11 letter slips (4864). DL-12 coat on the peg (5337). DL-14 chain rattle, random (5453). DL-15 duct crawl, random about 3/s (5642), and sitting on Mara's chair (5659). DL-17 key (5705). DL-14a hook (6048, 6060), and while the crank winds, random (6230). DL-14b figure (6107, 6364). DL-17 spindle (6212). Loose voice card taken up (6671) | one-shot | 1; −24.6 dBFS. Rev 0.2 | 2D | his claw touching something | `d17_tap` |
| rattle | `rattle(dur)` 616 | 0.5 s: opening frame 436 (1591). 0.9 s: DL-01 shutter release (1678) | one-shot | 1; −30 dBFS. Rev 0.4 | 2D | chain links rattling | `mech_rattle_500`, `mech_rattle_900` |
| step | `step(soft)` 617 | **Footsteps** at each half of the walk cycle (2073): soft = walk blend × 0.6 when crouched. Opening frames 444, 454 (0.7). Hopscotch hops (0.9; 3356, 3372) | one-shot, random pitch 900–1200 Hz | soft (0–1); −32 to −33 dBFS. Rev 0.25 | 2D | foot plant | `d17_step_v1..4` |
| jump | `jump` 618 | Jump (1994). Mantle (1910). DL-06 hop onto a carrier (2891). DL-08 jump to the platform (3334) | one-shot | 1; −36.7 dBFS. Rev 0.2 | 2D | take-off | `d17_jump` |
| land | `land(v)` 619 | Landing, v = min(1, 0.5 + fall height) (2026). Hop 0.6 (2892). DL-08 0.7 (3335). DL-07 end of the slide 0.6 (4508). Inside `death('fall')` at 1.4 | one-shot | v (0.5–1.4); −25.3 dBFS at 1 | 2D | landing | `d17_land` |
| lampClick | `lampClick` 620 | DL-01 cord lamp toggles (1867). A weight-lamp pip lights (6870) | one-shot | 1; −23.3 dBFS. Rev 0.4 | 2D | lamp on or off; amber pip | `mech_lamp_click` |
| buzzShort | `buzzShort` 621 | DL-01 cord lamp comes on (1867). DL-11 terminal "nobody" (3623). DL-10 UP refused (4590). DL-05 plate reads under, 350 ms (4897). DL-12 register (5390). DL-15 lift refuses (5716). DL-16a too heavy (6174). Pip flash, the warning (6873). `curio('switch')` | one-shot | 1; −34 dBFS. Rev 0.3 | 2D | refusal lamp blinking; lamp buzzing on | `elec_buzz_short` |
| ratchet | `ratchet` 622 | Crank strokes: DL-01 bulkhead (1889) and DL-10 door (4570). DL-05 hatch twitch, serve and wind (4901, 4910, 4917; random about 6/s while winding). DL-09 pawl bites (5092). DL-14 pole jam and blinds (5338, 5372, 5374). DL-15 lift moving, random 5/s (5722). DL-16 rack stores and winds (5757, 5766). DL-14a blinds (6092, 6094). DL-17 valve (6205). DL-16a catch (6242). Voice-card crank at 0.25 and 0.7 s (6669–6670) | one-shot (6 clicks, 70 ms apart) | 1; −29.5 dBFS. Rev 0.4 | 2D | crank turning; pawl teeth | `mech_ratchet` |
| doorRumble | `doorRumble` 623 | Each crank stroke on the DL-01 bulkhead (1889) and the DL-10 door (4570) | one-shot | 1; −24.5 dBFS. Rev 0.8 | 2D | the door lifting a quarter | `mech_door_rumble` (+`_wet`) |
| doorOpen | `doorOpen` 624 | DL-01 bulkhead fully open (1890, with the `threshold` cue). DL-10 striped door (4571). DL-14a door (6227) | one-shot | 1; −21.1 dBFS. Rev 1.0 | 2D | door opens | `mech_door_open` (+`_wet`) |
| strain | `strain` 625 | Mantle (1910). DL-09 hopscotch (3406). DL-07 bucket gate stops short (4831). DL-14 grind, 40 % of scrapes (5460). DL-14a heavy bag (6100) | one-shot | 1; −29.2 dBFS. Rev 0.3 | 2D | effort | `d17_strain` |
| drip | `drip(v)` 626 | DL-01 atmosphere: each falling drop lands (7904), every 2–5 s per drop, v = 1 − dist/6 | one-shot, random pitch 1400–2300 Hz, sliding to 2200 | v; −26 dBFS. Rev 0.9 | 2D, distance-scaled | drop hits the floor; ring ripple | `env_drip_v1..3` (+`_v1_wet`) |
| crackle | `crackle(v)` 627 | DL-01 live cable, every 3–8 s, v = max(0.15, 1 − \|8 − x\|/6) (7938). DL-09 tunnel live cable's tell, 0.4 (7407). Inside `death` crush (1), grabbed (0.8), fall (0.7) | one-shot, random | v; −25.5 dBFS. Rev 0.5 | 2D, distance-scaled | cable arcing | `elec_crackle_v1..3` |
| groan | `groan` 628 | Distant machinery: every 6–14 s in play, 40 % of the time, not under a moment (7964). DL-09 cage lurch and slip (5022, 5038). DL-13 brake (5354). DL-14a brake (6079). DL-17 no sluice open (6204). DL-07 gallery gives way (7355) | one-shot | 1; −34.2 dBFS. Rev 1.0 | 2D | structure under load (none for the distant one) | `env_groan` (+`_wet`) |
| scrape | `scrape` 638 | Opening frame 402. Mantle, 380 and 1050 ms (1910–1911). DL-03 weight lifted (2278). DL-08 crate down the chute (3136). Item picked up (4419). Cart or duct tips over (4739). DL-07 slide (4953). Weight tumbles (5000). DL-14 chain grinding against the pole, every 0.32 s (5460) | one-shot | 1; −33.7 dBFS. Rev 0.3 | 2D | dragging metal | `mech_scrape` |
| bonk | `bonk` 639 | Head hits the ceiling (2017) | one-shot | 1; −26 dBFS. Rev 0.4 | 2D | head bump | `d17_bonk` |
| creak | `creak(dur)` 640 | 0.3: DL-07 gallery sags, random (7366). 0.4: DL-01 cord (1873), DL-14a hook (6048, 6060). 0.5 (the default): DL-11 door (3666), DL-10 gate starts (4624), DL-14 window peel (5474). 0.6: DL-01 latch (1849), DL-07 bucket gate (4831), DL-17 float latch (6258). 0.7: DL-17 door (5789). 0.8: DL-09 cage settles (5033), DL-07 gallery goes (7355) | one-shot | 1; −28 dBFS. Rev 0.5 | 2D | slow hinge or strain | `mech_creak_300/400/500/600/700/800` (+`_wet` for 300, 600, 700, 800) |
| clank | `clank` 641 | DL-01 shutter release (1678). DL-06 carrier tips into the chute (2715). DL-09 plate into the tray (4435). DL-05 plate reads over (4898). DL-07 weight lands in the bucket (5003). DL-14 unjam and jam (5327, 5338). DL-16 rack latched (5764). DL-17 stamp (5779). DL-16a load (6158) and catch (6242). DL-14a door (6227). DL-17 float (6258). DL-02 franking press (7350). DL-07 gallery collapse (7361). `death('crush')` | one-shot | 1; −18.2 dBFS. Rev 0.8 | 2D | heavy metal hit | `mech_clank` (+`_wet`) |
| chain | `chain(dur)` 642 | 0.3: DL-02 tube coughs (4772), and inside `lurch`. 0.5: inside `liftCrash`. 0.55: DL-01 release (1678). 0.6: DL-07 gallery (7361). 1.0: DL-16a shoots up (6175). 1.2: DL-09 cage haul and lower (5027, 5036). 1.5: DL-05 served (4901). 2.0: DL-10 car up and down (4585, 4632), DL-16a down (6173). 2.2: DL-14 blinds (5372), DL-14a blinds (6092). 2.5: DL-09 haul after the crash (5049), DL-16 rack latched (5764). 3.0: DL-16a rise (6176) | one-shot (22 ticks, front-loaded) | 1; −29 to −32 dBFS. Rev 0.5 | 2D | chain running over a pulley | `mech_chain_300/500/550/600/1000/1200/1500/2000/2200/2500/3000` |
| thud | `thud` 643 | DL-01 shutter lands, 560 ms after release (1679). DL-07 onto the heap (2993). DL-04 drum set (4728). DL-01 cart into the trench (4757). DL-11 duct into the flood (4855). DL-07 weight in the bucket, 250 ms (5003). DL-13 a lesson step down (5425). DL-16 pit (5798). DL-14a bag (6049). DL-02 press (7350). DL-07 gallery (7362). `death('crush')` | one-shot | 1; −9.4 dBFS. Rev 0.9 | 2D | heavy impact; camera shake | `mech_thud` (+`_wet`) |
| distant | `distant` 644 | Distant machinery: every 6–14 s, 60 % of the time (7964). The prologue's end fade (8185) | one-shot | 1; −31.6 dBFS. Rev 1.0 | 2D | none (offscreen) | `env_distant` (+`_wet`) |
| plate | `plate` 646 | DL-03 pressure plate loaded (2375). DL-12 someone on the strip (5385). DL-15 seat lamp lights (5728) | one-shot | 1; −23.4 dBFS. Rev 0.6 | 2D | plate sinks; lamp | `mech_plate` (+`_wet`) |
| gateTick | `gateTick` 647 | DL-03 gate winding up, every 5 cm (2382). DL-08 platform rising, every 4 cm (3186). DL-07 bucket gate, random about 6/s (4830) | one-shot, random pitch | 1; −31 to −36 dBFS. Rev 0.5 | 2D | gate rising notch by notch | `mech_gate_tick_v1..3` |
| gateSlam | `gateSlam(v)` 648 | DL-03 gate drops, v = min(1, speed/3) (2386). DL-10 lift gate shuts, 1 (4626). DL-12 gate, 0.8 (5404) | one-shot | v; −11.9 dBFS | 2D | gate slams; shake | `mech_gate_slam` (+`_wet`) |
| lift | `lift` 649 | He lifts a carried thing (frame 13 of Lift): DL-03 weight (2277), chapter-one items (4418), DL-14 (5328), DL-15 tray (5668), DL-14a (6101), DL-16a (6139) | one-shot | 1; −30.6 dBFS | 2D | lift | `d17_lift` |
| setDown | `setDown(onDeck)` 650 | true (onto a deck): DL-03 trolley (2285), DL-09 tray (4435), DL-07 carrier tub (4452), DL-10 suitcase in the car (4560), DL-16a car (6158). false (onto the floor or a peg): DL-03 (2285), chapter-one items (4425), DL-02 tube letter lands (4779), DL-12 coat on the peg (5337), DL-14a (6047, 6060) | one-shot | 1; −13.6 (deck) and −15.8 (floor) dBFS. Rev 0.6 | 2D | put down | `d17_setdown_deck`, `d17_setdown_floor` (+`_wet`) |
| squeak | `squeak` 651 | Wheels, random: DL-03 and DL-08 trolleys (2350; about 0.6 or 1.2 /s while moving), DL-10 car moving (4637), pushing the body or courier (4703), DL-16 bridge (5753), DL-14b figure and trolley (6107, 6376, 6386) | one-shot, random pitch | 1; −38.5 dBFS | 2D | wheels | `mech_squeak_v1..3` |
| rowOn | `rowOn(i)` 670 | DL-04, the racks light row by row after the reveal, i = 0–5 at `ROW_TIMES` 1.0, 2.2, 3.4, 4.6, 5.8, 7.0 s (2422) | one-shot | 1; −25 to −29 dBFS. Rev 0.9 | 2D | a row of tubes lights | `mech_row_on_0..5` (+`_wet`) |
| knock | `knock` 671 | DL-03 pats (2287, 2306–2307). DL-08 (3341–3342). DL-11 knocks on C-114's door (3651–3652). Letter posted into a slot (4486) | one-shot | 1; −25.9 dBFS. Rev 0.5 | 2D | knuckle on metal | `d17_knock` |
| scanSweep | `scanSweep` 673 | DL-06 scanner sweep (2792) | one-shot, 1.6 s | 1; −30.5 dBFS. Rev 0.4 | 2D | scan bar moving down him | `mech_scan_sweep` |
| reject | `reject` 674 | DL-06 scanner refuses (2801), with the `dead` cue, then the `tan_scanner` voice | one-shot | 1; −20.9 dBFS. Rev 0.5 | 2D | scanner lamps go red | `mech_reject` (+`_wet`) |
| hatchLift | `hatchLift` 675 | DL-06/07 carrier rises through its hatch (2680, 2715, 2739) | one-shot, 1.2 s | 1; −36.8 dBFS | 2D | carrier rising | `mech_hatch_lift` |
| bell | `bell` 676 | DL-06 carrier docks (2701). DL-12 "present" (5393). DL-13 lesson start and each lesson (5411, 5421). DL-15 dismissal, twice 700 ms apart (5732). DL-16a pushes (6146, 6170). DL-14a door opens (6227). DL-14b trolley keeps a pupil (6387), or catches him or a figure, twice 260 ms apart (6396, 6405) | one-shot | 1; −27.9 dBFS. Rev 0.8 | 2D | dock lamp; school bell | `mech_bell` (+`_wet`) |
| klaxon | `klaxon` 677 | DL-06 belt starts (2822, 2932). DL-08 returns belt runs, at 2.7 s (3225) | one-shot | 1; −29.4 dBFS. Rev 0.7 | 2D | belt warning lamp | `mech_klaxon` (+`_wet`) |
| beltStop | `beltStop` 678 | DL-06 stop lever stops the belt (2932) | one-shot | 1; −23.9 dBFS | 2D | belt halts | `mech_belt_stop` (+`_wet`) |
| clunk | `clunk` 679 | Generic heavy stop. DL-06 levers and carriers (2715, 2739, 2924–2925). DL-08 platform at the top (3188). DL-10 car (4585, 4631, 4635). DL-04 cradle (4805). DL-05 hatch (4910, 4917). DL-09 cage caught (5048). DL-13 brake (5346). DL-16 lever (5691). DL-15 lift (5722). DL-16 bridge (5743). DL-16a (6176, 6236, 6237, 6244). DL-17 sluice and tank (6194, 6203, 6204). DL-14b figure (6363). DL-11 junction (7249). `curio('stamp')` | one-shot | 1; −18.6 dBFS. Rev 0.6 | 2D | something heavy stops | `mech_clunk` (+`_wet`) |
| clack | `clack(v)` 680 | DL-06 junction points: 0.4 as a carrier passes (2709), 1 when he throws the lever (2933). DL-15 figure detent (4720). DL-13 a lesson step up (5425) | one-shot | v; −19.3 dBFS. Rev 0.6 | 2D | points flip | `mech_clack` (+`_wet`) |
| tumble | `tumble` 681 | DL-07 weight tumbles into the bucket, 300 ms (2730). Onto the heap (2993). Gallery collapse (7362) | one-shot, random | 1; −32 dBFS | 2D | things tumbling | `mech_tumble_v1..2` |
| pawlClick | `pawlClick` 706–710 | DL-08 pawl latches the platform (3125, with the `latch` cue). DL-13 brake (5346, 5352). DL-14a brake (6079). DL-17 sluice (6194) | one-shot (3 stages, 0–205 ms) | 1; −12.2 dBFS. Rev 0.8 | 2D | pawl drops home | `mech_pawl_click` (+`_wet`) |
| pawlClatter | `pawlClatter` 711 | DL-08 the pawl rattles on the rack, frames 12 and 21 (3316–3317). DL-09 cage pawl misses or bites (5092–5093) | one-shot, random | 1; −24 dBFS | 2D | pawl skipping | `mech_pawl_clatter_v1..3` |
| liftCrash | `liftCrash(v)` 712 | DL-08 platform drops onto its buffers, v = min(1, speed/3) (3193). DL-09 cage dip 0.4 (5026) and crash 1 (5043). It also plays `chain(0.5)` unscaled | one-shot | 1 file per v; DL-08's runtime v: use `mech_lift_crash` at volume v (its chain then scales too, a slight deviation); −6.6 dBFS | 2D | crash; big shake | `mech_lift_crash`, `mech_lift_crash_v040` (+`_wet`) |
| lurch | `lurch` 713 | DL-08 teeter (3281). DL-09 cage dip, shudder, stall (5022, 5037, 5041). Includes `chain(0.3)` | one-shot | 1; −18.1 dBFS | 2D | lurch; shake | `mech_lurch` (+`_wet`) |
| alarmBell | `alarmBell` 714 | DL-08 returns-belt warning at 0, 0.9, 1.8 s (3224). DL-05 plate reads over, 300 ms (4898). DL-09 cage dip (5026). DL-11 doorbell: a trill every 0.55 s while it rings (7257) | one-shot (9 strikes, 55 ms apart) | 1; −25.7 dBFS. Rev 0.7 | 2D | bell hammer; red lamp | `mech_alarm_bell` (+`_wet`) |
| crateLand | `crateLand(v)` 715 | DL-08 crate drops onto the belt, v = max(0.2, 1 − \|x − crate x\|/8) (3157) | one-shot | v; −20.1 dBFS | 2D, distance-scaled | crate lands | `mech_crate_land` (+`_wet`) |
| found | `found` 742 | A curiosity found for the first time (6707). A voice card heard for the first time (6676) | one-shot | 1; −29.2 dBFS. Rev 0.8 | 2D (UI) | the ◆ counter appears | `curio_found` (+`_wet`) |
| curio | `curio(kind)` 743–754 | At frames of his curio clip (`CURIOS[].cues`, 5104–5118; 24 fps):<br>• scale: DL-01 scale, frame 30<br>• paper: DL-01 dispatch sheet, frames 19 and 62<br>• stamp (= clunk + thud noise): DL-02 franker, frame 30<br>• mug and mugDown: DL-02 tea corner, frames 26 and 76<br>• sit: DL-04 rack (frame 50) and DL-06 chair (frame 58)<br>• wind: DL-07 clock, frame 12<br>• coin: DL-09 coin viewer, frame 58<br>• radio: DL-11 radio, frame 34 (then the `radio_above` voice)<br>• switch (= noise + buzzShort): DL-11 switch, frame 16 | one-shot | 1; −18 to −32 dBFS | 2D | the curio clip's prop moving | `curio_scale`, `curio_paper`, `curio_stamp` (+`_wet`), `curio_mug` (+`_wet`), `curio_mug_down`, `curio_sit`, `curio_wind`, `curio_coin`, `curio_radio` (+`_wet`), `curio_switch` |
| radio | `radio` 756–761 | Through `curio('radio')`: static (1.2 s), then the children's tune, 15 steps 300 ms apart from 1.3 s, then static (0.8 s) | one-shot, 6.4 s | 1; −28.1 dBFS | 2D | radio dial glowing | `curio_radio` (+`_wet`) |
| splash | `splash(v)` 763 | Water:<br>• DL-11 duct into the flood, 1.3 (4855)<br>• DL-09 cage into the sump, 1.5 (5045)<br>• DL-17 valve, 0.5 (6205), and rig water, random about 8/s at 0.15 (6253)<br>• the White: warning 1 (7152), strike 1.2 (7157), drag 1.5 (7166), under 1 (7172)<br>• DL-11 junction, 0.6 (7249)<br>• the White shows itself, 0.5 (DL-11 7272, DL-08 7372)<br>• DL-08 sump fall, 1.4 (7374)<br>• `death('grabbed')`, 1.2 | one-shot | v (0.15–1.5); −19 dBFS at 1. Rev 0.9 | 2D | splash; ripples | `env_splash` (+`_wet`) |
| zap | `zap(v)` 764 | DL-11 junction thrown, 1.4, 250 ms (7249). DL-09 tunnel live cable: 0.7 when live (7406), 1 on the first touch (7411). `death('shock')`, 1.2 | one-shot, random | v; −17 to −19 dBFS | 2D | arc and sparks | `elec_zap_v1..3` (+`_v1_wet`) |
| death | `death(how)` 765–771 | `die()` (7441). Each also plays "his voice running down", a sine 880 → 110 Hz at 120 ms:<br>• crush: DL-02 franking press (7351)<br>• shock: DL-09 live cable, second touch (7412)<br>• grabbed: the White's strike (7164), DL-08 sump fall (7374)<br>• fall: riding the DL-09 cage down (5045) | one-shot, random | 1; −6.5 to −21 dBFS | 2D | death clip and spark burst; cut to respawn | `death_crush/shock/grabbed/fall_v1..2` (+`_v1_wet`) |

## Sound: continuous layers

Each is a graph built once, whose gain glides to `level × scale` with `setTargetAtTime` (time constant τ). In Unity,
use a looping AudioSource at volume `level` with the same glide: a one-pole smoothing, 63 % in τ. The loops are
rendered at level 1, so they include the scale.

| Sound | Source | Graph | Level mapping (call line) | τ | Space | Visual equivalent | Output |
|---|---|---|---|---|---|---|---|
| hum | `start` 576–579, `hum` 604 | 50, 100, 150 Hz sines (gains 0.5, 0.25, 0.08) + noise 0.06 → lowpass 180 Hz; scale 0.12 | Opening: 0.25 at frame 0, 0.5 at 120, 1 at 168 (1582–1584). Play: 1 (8104). DL-08: 1 − 0.8·smooth((x − (OFF3 + 60))/8). Ring C: 0.2 (3253–3254) | 0.4 s | 2D | the depot's power (lights on) | `loop_hum` (2 s) |
| buzz | `start` 580–582, `buzz` 605 | 120 Hz sawtooth → bandpass 240 Hz, Q 3; scale 0.03 | DL-01 work bulb: `bulb` during its flicker (opening frames 226–252), else bulb × 0.25 (1574) | 0.01 s | 2D | work bulb flicker | `loop_buzz` (2 s) |
| hiss | `hiss` 629–637 | noise → highpass 2500 Hz; scale 0.03 | DL-01 steam: max(0, 1 − \|8.7 − x\|/2.5) in play × `atmos.hissLevel` (7965). The White's warning: 1 for 0.9 s, then 0 (7152). Both set the same node | 0.2 s | 2D, distance-scaled | steam wisps; the White rearing | `loop_hiss` (2 s) |
| roll | `roll` 652–660 | noise → lowpass 260 Hz; scale 0.22 | DL-03 trolley: min(1, \|speed\|/0.5) while pushed (2370). DL-06 riding a carrier: 0.7 (2969). DL-08 trolley: min(1.2, \|speed\|/0.3) (3178) | 0.06 s | 2D | wheels rolling | `loop_roll` (2 s) |
| tubes | `tubes` 661–669 | 120 Hz sawtooth → bandpass 480 Hz, Q 2; scale 0.006 | DL-04 racks: lit × max(0.25, 1 − \|x − (OFF2 + 21)\|/8) in region 2 (2428) | 0.3 s | 2D, distance-scaled | lit tube rows | `loop_tubes` (2 s) |
| belt | `belt` 682–692 | noise × (0.5 + 0.4 sin 9 Hz) → bandpass 900 Hz, Q 0.8; scale 0.05 | DL-06: running × max(0.2, 1 − \|x − (OFF3 + 33)\|/9) (2830). DL-08 returns belt: max(0.12, 1 − \|x − (OFF3 + 61)\|/7) while running (3229) | 0.25 s | 2D, distance-scaled | belt running | `loop_belt` (2 s) |
| drum | `drum` 694–705 | noise × (0.5 + 0.5 sin 16 Hz) → bandpass 2300 Hz, Q 1.2, + 62 Hz triangle 0.6; scale 0.07 | DL-08 lift drum: min(1, platform speed/0.6) (3200) | 0.08 s | 2D | drum and chains turning | `loop_drum` (2 s) |
| air | `air` 716–727 | noise × (0.7 + 0.3 sin 0.09 Hz) → lowpass 420 Hz; scale 0.09; **send 0.6 to the depot reverb** | DL-09: smooth((x − (OFF4 + 65))/6). Ring C: 1 − 0.7·smooth((x − (OFF5 + 80))/2) (3255) | 0.8 s | 2D | the refuge's open air | `loop_air` (11.11 s), `loop_air_wet` |
| drag | `drag` 729–740 | noise × (0.5 + 0.35 square 23 Hz) → bandpass 1100 Hz, Q 1.6; scale 0.12; **send 0.4** | DL-11 desk: min(1, speed/DRAG_SPEED) (3543). Body and courier push: min(1, speed/0.22) (4703); 0 at the end of travel (4727–4733, 4790). DL-17 drawer: 0.6, then 0 (5696–5697) | 0.06 s | 2D | dragging a desk or body | `loop_drag` (2 s), `loop_drag_wet` |

`setEnabled(on)` (603) is the options toggle. It glides the master to 0 or 0.8 with τ 0.05 s; this belongs to the
Unity mixer, so it has no file.

## Ambience: positional emitters (index.html 1145–1211; placement 6577–6598)

`Ambience.update` runs every frame in play (8525). For each emitter in his region (and on his deck, `upper`, when it
is set), it computes k = max(0, 1 − \|x − e.x\|/reach) and glides the emitter's gain to `level × k²` with τ 0.25 s.

- Out of reach, the gain fades (τ 0.3–0.4 s) and the graph is freed 3 s later.
- **Continuous kinds** are one graph: one loop file, volume = level × k².
- **Event kinds** schedule blips while in reach. Each blip returns the delay to the next one. In Unity, use a timer
  with the same random interval, play a random take, and set its volume to level × k².

| Kind | Source | Graph or blip | Interval | Type | Output |
|---|---|---|---|---|---|
| buzz | `make` 1161–1165 | 100 Hz sawtooth → bandpass 1800 Hz, Q 4, × (0.05 + 0.03 sin 0.13 Hz) | continuous | loop | `amb_buzz_loop` (7.7 s) |
| hum | `make` 1161–1164 | 50 Hz sawtooth → bandpass 160 Hz, Q 1.2, × 0.12 | continuous | loop | `amb_hum_loop` (2 s) |
| lap | `make` 1166–1171 | noise → lowpass 520 Hz, Q 0.8, × (0.16 + 0.1 sin 0.31 Hz) | continuous | loop | `amb_lap_loop` (6.45 s) |
| wind | `make` 1166–1172 | noise → lowpass (380 + 160 sin 0.05 Hz), Q 0.8, × (0.2 + 0.12 sin 0.07 Hz) | continuous | loop | `amb_wind_loop` (20 s, 2 s crossfade) |
| machine | `make` 1166–1173 | noise → lowpass 90 Hz, Q 0.8, × (0.35 + 0.08 sin 0.9 Hz) | continuous | loop | `amb_machine_loop` (10 s) |
| static | `make` 1166–1170 | noise → bandpass 2400 Hz, Q 0.5, × 0.05 | continuous | loop. **Not placed** in `EMITTERS` today | `amb_static_loop` (2 s) |
| drip | `blip` 1179 | sine 1400–2100 Hz → 380 Hz over 70 ms, gain 0.25 → 0.001 over 120 ms | 0.7–2.9 s | one-shot, random | `amb_drip_v1..3` |
| tick | `blip` 1180 | square 2400 Hz, 0.06 → 0.001 over 20 ms | `e.period` (0.9 or 0.25 s) | one-shot | `amb_tick` |
| fan | `blip` 1181 | triangle 220–250 Hz, 0.05 → 0.001 over 50 ms | 0.9–3.4 s | one-shot, random | `amb_fan_v1..3` |
| musicbox | `blip` 1182–1191 | 11 notes on 1046.5 Hz × 2^(n/12), n = 0 4 7 9 7 4 2 4 0 −3 0: sine 0.12 over 1.4 s, plus its third harmonic ×3.01 at 0.03 over 0.5 s. Then 4 rests of 0.6 s | notes (0.42–0.48 s) × `slow` | loop (one turn of the tune) | `amb_musicbox_loop` (7.43 s) |

The placed emitters (`EMITTERS`, 6577–6598; all spatial, positional on x):

| Scene | x | Kind | Level | Reach | Condition | Visual equivalent (audio_audit.md) |
|---|---|---|---|---|---|---|
| DL-01 | 1.0 | tick, period 0.9 | 0.45 | 3 | | the dispatch board's blinking lit line |
| DL-01 | 7.3 | drip | 0.7 | 4.5 | | the burst pipe into the trench |
| DL-02 | 19.8 | fan | 0.6 | 4.5 | | the stopped fan's loose blade |
| DL-02 | 23.4 | buzz | 0.5 | 4 | | a fluorescent tube under the gantry |
| DL-04 | 36.0 | buzz | 0.35 | 5 | after the reveal | a failing tube in the racks |
| DL-05 | 56.2 | drip | 0.55 | 4 | | the ration hall's tap |
| DL-06 | `SCANNER_X` | hum | 0.5 | 3.5 | lower deck | the scanner's mains |
| DL-07 | OFF3 + 37.8 | lap | 0.35 | 4 | lower deck | the heap's water |
| DL-08 | shaft middle | lap | 0.8 | 4.5 | | the sump (the White's water) |
| DL-09 | 107.17 | musicbox | 0.5 | 3.2 | | the den's music box, the cue to the vent |
| DL-09 | 114.5 | wind | 0.6 | 6 | | the balcony |
| DL-11 | OFF5 + 94.3 | lap | 0.6 | 5 | | the flooded lane |
| DL-11 | 150.0 | lap | 0.45 | 6 | | the lane further on |
| DL-11 | 170.85 | hum | 0.45 | 3 | | the new splice box |
| DL-11 | 174.5 | wind | 0.7 | 4.5 | | the well, at the end |
| DL-12 | 205.0 | buzz | 0.3 | 6 | | school tubes |
| DL-13 | 224.0 | tick, period 0.25 | 0.5 | 7 | lesson running, not braked | the lesson apparatus's clockwork |
| DL-13 | 224.0 | machine | 0.35 | 6 | the same | the apparatus running |
| DL-14 | 238.0 | buzz | 0.25 | 6 | | school tubes |

Chapter 2's emitters (`SomeoneHomeEmitters`, region 7; no prototype, from DL-18 §8 and DL-19 §3/§8). The relay boxes'
click every 7 s is not an emitter: `SomeoneHomeSounds` plays it on the game clock, in step with their pilot lamps.

| Scene | x | Kind | Level | Reach | Condition | Visual equivalent |
|---|---|---|---|---|---|---|
| DL-18 | 348.0 | buzz | 0.15 | 3 | | a gallery lamp (maintained, faint buzz) |
| DL-18 | 350.4 | buzz | 0.15 | 3 | | the other gallery lamp |
| DL-18 | 349.5 | wind | 0.3 | 5 | | the shaft's air below the gallery |
| DL-18 | 351.95 | tick, period 1 | 0.5 | 3.5 | `clockTicking`: not while it rings | the alarm clock |
| DL-18 | 358.0 | wind | 0.25 | 6 | | the shaft at the terrace landing |
| DL-19 | 372.0 | wind | 0.3 | 6 | | the shaft beyond the upper terrace's rail |

## Voices (index.html 966–1143)

**No recordings exist yet.** `game/undelivered/assets/voice/` is absent, so every voice plays its placeholder murmur.
Nothing processed can be rendered, so the chain is documented below for Unity to rebuild as a mixer effect chain on
each voice's AudioSource. The parts that are synthesis, not processing, are rendered: the tannoy chime, the crackle
beds and the room impulses.

### The chain (`chain` 1024–1042, `play` 1059–1131)

The signal path is: source → head gain 0.9 → waveshaper → highpass → lowpass → (ring modulator) → mix → dry 1, plus a
convolution room, plus an echo → out (the voice's level × positional k) → voice bus (1) → master.

- **Rate and pitch.** `playbackRate = rate × 2^(pitch/12)`, which changes speed and pitch together, like tape.
- **Wow and flutter.** These modulate the source's detune in cents:
  - wow: a 0.55 Hz sine at ±`wow` cents;
  - flutter: a 7.3 Hz sine at ±`wow × 0.25` cents;
  - `tremble` adds a 5.2 Hz sine at ±14 cents.
  - In Unity, modulate the AudioSource's pitch: cents → ratio 2^(c/1200).
- **Saturation.** A waveshaper with curve `tanh(x · drive) / tanh(drive)` over 1024 points in −1..1, with no
  oversampling.
- **Band-pass.** A highpass at `lo` (Q 0.7), then a lowpass at `hi` (Q 0.9). Both are WebAudio biquads (RBJ cookbook),
  12 dB/oct each. Unity's Highpass and Lowpass effects with resonance Q 0.7 and 0.9 match these.
- **Ring.** Where `ring` is set, the gain is 0.75 + 0.25 × sin(2π · ring · t): amplitude modulation, not full ring
  modulation.
- **Room.** A convolver whose impulse is stereo noise × (1 − t/T)^3 over T = `room` seconds, with the return gain
  `wet`, or min(0.6, 0.18 + 0.12 × room) when `wet` isn't set. The impulses are `ir/ir_voice_<ms>.wav`.
- **Echo.** Where `echo` is set: a delay of `echo` s → lowpass 1900 Hz → feedback 0.22 back into the delay; the
  output is taken after the lowpass, at 0.32.
- **Crackle bed.** Under every voice, unprocessed, straight into out:
  - a 3 s looped buffer of noise ±0.08, with clicks of ±0.4–1.0 at a probability of `crackle × 40 × 0.02` per sample;
  - → highpass 900 Hz → gain `crackle × 2.2`.
  - Rendered per treatment as `voice_crackle_<treat>.wav`: a 3 s loop, at its gain, before the voice's level.
- **Static swell** (radio only). Noise → bandpass 2200 Hz, Q 0.6. Its gain runs 0.12 → 0.05 (linear, at 30 % of the
  voice's length) → 0.55 (linear, at its end + 0.6 s). The automation depends on the voice's length, so it is
  runtime-only.
- **Chime** (tannoy only, not when stuck). Two notes into the chain head:
  - 659.3 Hz at 0.05 s and 523.3 Hz at 0.6 s;
  - each is a sine plus a ×2.01 partial at 0.18, with gain 0.0001 → 0.32 linear over 12 ms → 0.0001 exponential by
    1.1 s;
  - the voice starts at 1.35 s; without a chime, at 0.25 s.
  - Rendered as `voice_tannoy_chime.wav`: through the tannoy chain (shaper, band, room, echo), out gain 1, 1.79 s,
    stereo.
- **Level.** The out gain glides to the voice's level with τ 0.08 s.
  - Positional voices then follow `level × max(0, 1 − |x − v.x|/reach)` (τ 0.15 s), and stop once it reaches 0.
  - Music ducks to 0.4 under any voice (τ 0.4 s down, 1.5 s up).
  - `stop(fade)` fades with τ fade/4.
  - One voice plays at a time.
- **Card files.** A card with several files (`card_den`) plays them in turn, with 0.15 s gaps.
- **Placeholder murmur** (runtime: random, shaped to each line's subtitle timing; used until recordings exist):
  - a sawtooth (square for `machine`) at f0, where f0 is 128 (machine), 265 (child), 112 (elder), 138 (tannoy) or
    165 Hz;
  - through two bandpass formants (Q 7 and 9, gains 2.2 and 1.4), jumping between 8 vowel pairs for each syllable;
  - syllables = round(words × 1.4) per line, over the line's length less 0.45 s;
  - the pitch falls through each phrase.

| Treatment | rate | pitch (st) | lo / hi (Hz) | drive | crackle | wow (cents) | room (s) / wet | extras |
|---|---|---|---|---|---|---|---|---|
| tannoy | 1 | 0 | 380 / 3400 | 1.6 | 0.005 | 2 | 1.4 / 0.2 | chime; echo 0.23 s |
| dispatch | 1 | 0 | 330 / 3600 | 1.3 | 0.003 | 0 | 1.2 / 0.18 | ring 47 Hz; echo 0.23 s; machine voice |
| card | 1 | 0 | 250 / 3500 | 1.6 | 0.02 | 9 | 0.5 / 0.24 | |
| card_worn | 0.97 | 0 | 300 / 3000 | 2.2 | 0.045 | 18 | 0.5 / 0.24 | `drops: true` (declared, not used by `play`) |
| child | 1.06 | +4 | 250 / 3800 | 1.6 | 0.02 | 9 | 0.6 / 0.252 | |
| elder | 0.95 | −1.5 | 250 / 3300 | 1.6 | 0.025 | 12 | 0.5 / 0.24 | tremble 5.2 Hz ±14 cents |
| machine | 1 | 0 | 600 / 2600 | 3 | 0.006 | 0 | 0.9 / 0.288 | ring 31 Hz; machine voice |
| radio | 1 | 0 | 500 / 2800 | 3 | 0.08 | 6 | 0.2 / 0.204 | static swell |

### Voice assets and cues

The text is in `VOICE_LINES` (6522–6554), and the script in `docs/voice_script.md`. The expected recordings are
`assets/voice/<id>.mp3` or `.wav`.

- **Length** is the sum of the subtitle lines. With a recording, the subtitles stretch to the recording's length.
- **Level** is the `play` option. Positional voices also take their reach.
- Tannoys (`updateTannoys`, 6679) play once as he comes within `trigger` of `at ?? x`. They play again, at 0.5 instead
  of 0.85, only if he has gone beyond `reach` and come back more than 150 s later. They don't play while a voice or a
  directed moment's shot holds (`voicesHeld`).

| Id | Treat | Lines / length | Where and when (line) | Level, reach |
|---|---|---|---|---|
| dispatch_wake | dispatch | 2 / 4.6 s | DL-01 opening, frame 204 (8.5 s) (1586) | 0.8, 2D |
| dispatch_item | dispatch | 2 / 6.4 s | start of play, over his look at the label (8109) | 0.8, 2D |
| tan_depot_1 | tannoy | 5 / 15.8 s | DL-01 tannoy x 1.69, plays from x 8.6 ± 0.6 once released | 0.85 / 0.5, reach 14 |
| card_sorter | card | 6 / 26 s | DL-02 tea corner player, x 16.6 (wind) | 1, reach 6 |
| tan_racks | tannoy | 6 / 11 s | DL-04 x 38.2 ± 3.0, after the reveal | 0.85 / 0.5, reach 9 |
| tan_rations | tannoy | 4 / 15.6 s | DL-05 x 56.6 ± 2.6 | 0.85 / 0.5, reach 9 |
| card_queue | card_worn | 5 / 20 s | DL-05 loose card x 51.55 | 1, reach 6 |
| tan_scanner | machine | 1 / 3 s | DL-06 scanner rejects (2801) | 0.8, reach 6 |
| card_reader | elder | 6 / 27.5 s | DL-06 secret room "the one who stayed" (6497, 6630) | 1, 2D |
| card_heap | card | 5 / 21 s | DL-07 player x 68.0, lower deck | 1, reach 6 |
| card_den | child (3 files) | 9 / 25.2 s | DL-09 secret room "the den" (6502) | 1, 2D |
| tan_bridge | tannoy | 3 / 12.5 s | DL-09 x 116.1 ± 2.4 | 0.85 / 0.5, reach 7 |
| tan_relocation | tannoy | 4 / 15.9 s | DL-10 x 120.45 ± 2.2 | 0.85 / 0.5, reach 9 |
| card_lastcar | card | 5 / 22.5 s | DL-10 loose card x 121.74 | 1, reach 6 |
| radio_above | radio | 4 / 10.8 s | DL-11 radio curio (6724), after `curio_radio` | 0.9, 2D |
| card_mara_parent | card | 6 / 30 s | DL-11 C-114 hall table x 158.07 | 1, reach 6 |
| att_gate_1/2/3 | tannoy | 1 / 3.2, 2.0, 2.4 s | DL-12 register: present (1 the first time, 2 after); 3 when coat and pupil are both in (5391, 5393) | 0.8, 2D |
| att_caretaker | elder | 5 / 21.6 s | DL-12 secret room "lost property" (6506) | 1, 2D |
| att_lesson | card | 5 / 18 s | DL-13 each lesson, if he is in the room (5421); braked: loops 0.35 s from 9.2 s, "…grows… grows…" (5358, `stickAt`) | 0.75 (stuck 0.7), reach 11 / 10 |
| att_rest | tannoy | 3 / 7.4 s | DL-14a x 250.6 ± 2.0, until the door opens | 0.85 / 0.5, reach 12 |
| att_trolley | machine | 1 / 3 s | DL-14b trolley finds him (6400) or a figure (6408) | 0.8 / 0.7, reach 9 |
| att_escort | card_worn | 6 / 21 s | DL-15 secret "under the balcony" (6516) | 1, 2D |
| att_bell | tannoy | 4 / 10.2 s | DL-15/16 x 295.4 ± 1.2, after the dismissal | 0.85 / 0.5, reach 12 |
| att_volunteer | elder | 7 / 28.8 s | DL-17 card x 332.0 | 1, reach 6 |
| att_teacher | card | 6 / 31 s | DL-14 secret "the stock cupboard" (6510) | 1, 2D |

Winding a card's player plays `ratchet` at 0.25 and 0.7 s and starts the voice at 1.2 s; a loose card plays `tap`
and starts at 0.9 s (6656–6677). The first hearing plays `found`.

### Letters

`game/undelivered/assets/letters/*.png` are images (the letters and records read in close-up), with no audio.

- Their sounds: `servo(0.35, 900, 1500, 0.02)` when the close-up scans, then `tap` on pick-up and `knock` + `chirp` on
  posting.
- Their cues: none. Letters don't trigger music.

## Music (files: `game/undelivered/assets/music/`)

Music is already MP3. `Music` (780–943) plays one **cue** at a time and, under it, one looping **ambience**:

- **Fades.** Cues fade in linearly over 1.2 s (or as asked) to their `LEVEL`. A cue that starts while another plays
  fades that one out over 1.5 s.
- **Handovers.** At `HAND[name][0]` seconds into a cue, the scene's loop comes in from its loop start under the cue's
  tail, fading in over 1.5 s. If the cue has intro bars (`HAND[name][1]` = 1), the loop also fades out across them
  (4 s a bar).
- **Ambience.** Changes crossfade over 4 s in and 4 s out (linear in, τ = out/4). It hides while a cue plays,
  fading out over 1.5 s.
- **Loops.** Each is looped between `loop` [start, end] seconds: the files are padded 2 s at each end so the decoder's
  priming misses the seam.
- **Bus.** Music bus = enabled × (paused ? 0.45 : 1) × duck (0.4 under a voice), then a compressor (threshold −24 dB,
  knee 12, ratio 4, attack 0.25 s, release 1.2 s) → master.
- **Directed moments** (`kin`, `refuge`, `ringc`, `window`) start at full level 0.1 s ahead, with no fade, and drive
  the camera from the cue's audio clock (`momentTime`). The timings are below.

| Key | File | Length | Level | Handover (s, intro) | Trigger (line) |
|---|---|---|---|---|---|
| wake | prologue_cue_wake | 54.0 s | 0.9 | 48, 0 | the opening starts, fade 0.6 (8068), under ambience lower_works |
| hall | prologue_cue_hall | 38.0 s | 0.9 | 32, 1 | DL-01: first past `HALL_X` before the bulkhead opens (2066) |
| threshold | prologue_cue_threshold | 30.0 s | 0.9 | 24, 1 | DL-01: bulkhead fully open (1890) |
| racks | prologue_cue_racks | 42.0 s | 0.9 | 36, 1 | DL-04: the reveal, fade 0.6 (2403) |
| kin | prologue_cue_kin | 34.0 s | 0.9 | 28, 0 | DL-04 `realise`: moment (1958) |
| dead | prologue_cue_dead | 46.0 s | 0.9 | 40, 0 | DL-06: scanner rejects, fade 0.15 (2801) |
| latch | prologue_cue_latch | 14.0 s | 0.9 | 8, 0 | DL-08: pawl latches, fade 0.15 (3125) |
| refuge | prologue_cue_refuge | 30.0 s | 0.9 | 24, 0 | DL-09: awe stop at `AWE_X`: moment (3433) |
| ringc | prologue_cue_ringc | 30.0 s | 0.9 | 24, 0 | DL-10: UP while riding: moment (4588) |
| childP | prologue_cue_child | 42.0 s | 0.9 | 36, 0 | DL-11: the desk's marks revealed (3547) |
| window | prologue_cue_window | 26.0 s | 0.9 | 20, 0 | the end: the look up the well: moment (2105) |
| end | prologue_cue_end | 66.0 s | 0.9 | 60, 0 | `finish()`: queued, or 5.2 s after `window` (8188–8189) |
| child | dl05_child | 50.1 s | 0.6 | none | DL-14 window peel, fade 2.5 (5474). DL-15 dismissal, fade 3 (5734) |
| endAtt | dl01_end | 100.0 s | 0.6 | none | chapter one's `finish()` |
| bed (loop 2–50 s) | dl01_bed | 52.0 s | 0.26 | none | chapter one, region 6: `Music.bed(true)`, fade in 6 s, out 3 s (8092, 5765); off at the dismissal and the DL-16 rack (5734, 5760) |
| lower_works (loop 2–34 s) | prologue_loop_lower_works | 36.0 s | 0.9 | none | `sceneAmbience()` (8146–8160): DL-01–03; DL-08; DL-09 until the cage is caught; DL-06 after the scan |
| order (loop 2–34 s) | prologue_loop_order | 36.0 s | 0.9 | none | DL-05 ration hall; DL-06 before the scan; DL-09 after the awe stop; DL-10 lobby |
| heaps (loop 2–34 s) | prologue_loop_heaps | 36.0 s | 0.9 | none | DL-04 racks after the reveal; DL-10 while riding (scale 0.6); ring C (scale 0.6) until the bedroom |
| failure (loop 2–34 s) | prologue_loop_failure | 36.0 s | 0.9 | none | DL-09 while the cage is in danger (fade in 1 s, out 2 s) |

The levels of the loops and cues in LUFS, and the theme's structure, are in `docs/prologue_music.md`.

**Directed moments** (`docs/directed_moments.md`; `MOMENTS`, 948). Times are seconds from the trigger, which is the
cue's own clock.

| Moment | Cue | Lock | Release | Control | Peak frame |
|---|---|---|---|---|---|
| One of many (DL-04) | kin | 19 | 21 | 22.5 | the wide over the racks at 15 |
| The city (DL-09) | refuge | 14 | 16 | 18.5 | the widest frame at 10 |
| Ring C (DL-10) | ringc | 16 | 20 | 22 | the light full on the lane at 12; the chime alone at 9.5 |
| The lit window (end) | window | 99 | 13.6 | 99 | the window at 6.5; the label check at 13.6 |

During a moment's shot, voices are held off (`voicesHeld`), and `Voice.stop(1.0)` runs at the trigger.

**Files not referenced** by the game today: `dl01_dead`, `dl01_hall`, `dl01_kin`, `dl01_racks`, `dl01_threshold`,
`dl01_wake`, `dl04_latch`, `dl04_refuge`, `prologue_lastcar` and `prologue_collapse`. These are the older score, and
the two DL-10 cues that `ringc` replaced. Don't import them unless the director wants them.

## Chapter 2 (DL-18, DL-19): sounds and wanted assets

Chapter 2 has no prototype, so it has no `Sound.*` calls to port. `SomeoneHomeSounds` (issue #57) plays existing bank
keys at the moments the scene docs' §8 name, read from the scenes' cues and the mechanisms' events:

| Moment | Source | Plays now | Wanted asset (not made yet) |
|---|---|---|---|
| The bed folds or unfolds from rest | `dl18.bed` state | `mech_creak_800` | `mech_bed_springs`: a fold bed's coil springs, 1.4 s |
| The bench folds or unfolds from rest | `dl18.bench` state | `mech_chain_1200` | (fits: "the bench's chains") |
| A leaf reaches its stop | `dl18.bed`/`bench` Down, Folded | `mech_clunk` (0.7 / 0.6) | |
| A leaf meets the heaped quilt | `FoldingLeafEvent.Met` index 0 | `mech_thud` at 0.35 | `env_quilt_thump`: a soft, muffled thump |
| A leaf meets D-17 and waits | `Met` index 1 | `d17_tap` at 0.6 | |
| The slide-off rocks | cue `dl18.bench.rock` | `mech_creak_500` | |
| The slide-off's soft bump | cue `dl18.bench.slide` | `mech_scrape` 0.5, `d17_land` 0.5 | |
| A tug at the Works door's chain | cue `dl18.chain.clank` | `mech_clank`, `mech_rattle_500` | |
| The alarm clock rings, 2 s | cue `dl18.clock.ring` | `mech_alarm_bell` at 0, 0.55, 1.1, 1.65 s | `mech_clock_ring`: a wind-up alarm clock's bell, 2 s |
| He pats it still | cue `dl18.clock.still` | `d17_tap` | |
| The sketch's close look | cue `dl18.sketch.look` | `curio_paper` | |
| The relay boxes, every 7 s | game clock, within 6 m of 349.4 or 370.4 | `mech_click` at 0.5·k | |
| The jack's wheels drop into the pocket | `RatchetJackEvent.Clunk` | `mech_clunk` | |
| A ratchet notch (0.02 m) | `RatchetJackEvent.Click` | `mech_gate_tick` (0.8 up, 0.6 down) | `mech_jack_click_v1..3`: one ratchet pawl click |
| The jack binds at its top | `Bind` | `mech_clunk` 0.5, `d17_strain` 0.6 | |
| He heaves at the loaded jack | `Heave` | `d17_strain` | |
| The jack rolls | its velocity > 0.05 m/s, about 0.8 /s | `mech_squeak` | |
| The loaded bent pin draws and bites | `BracketPinsEvent.Draw` | `mech_scrape` | |
| Use on a biting pin | `Strain` | `d17_strain` | |
| The slack pin drops into the tin cup | `Clink` | `mech_clack` at 0.4 | `mech_pin_clink`: a steel pin into a tin cup |
| He takes the spare | `Taken` | `d17_tap` | |
| The spare seats: a clean double click | `Seated` | `mech_click`, again 0.12 s later | |
| The spare chatters against the lug | `Chatter` | `mech_pawl_clatter` | |
| The bent pin under load, on a slow sway | `PinSound.Creak`, every 3.2 s within 6 m | `mech_creak_600` | `mech_pin_creak_v1..3`: a strained pin creaking with a sway |
| The slack pin | `PinSound.Rattle`, the same | `mech_rattle_500` | `mech_pin_rattle`: a loose pin rattling in its fork |
| The half landing drops onto the stops | `HalfLandingEvent.Drop` index 0 | `mech_clank`, `mech_thud` 0.5 (by speed) | |
| It drops onto the bent pin, or the saddle | `Drop` index 1, 2 | `mech_clank`, `mech_clunk` | |
| Step on: it lurches | cue `dl19.lurch` | `mech_lurch` | |
| Step on: it rocks on the stops and clangs | cue `dl19.rock` | `mech_lurch`, `mech_clank` | |
| `Settle`: the knee dip's servo whine | cue `dl19.settle` | `mech_servo_300_300_420` at 0.6 | `d17_servo_settle`: a quiet, short whine (never comic) |
| The drip tube, once a minute | cue `dl19.drip`, within 6 m of 363.4 | `env_drip` | |

Not sounds here: `held` (a low warm chord under the music box's three parcel notes, DL-19 §8: a music cue, still to
score) and `witness` (a shot). The chapter's music bed (DL-18 §8) is the music director's.

## Totals

- **Rendered:** 228 files, 27.9 MB, in `art/sfx/out/` (listed in `manifest.json`).
  - 61 `Sound` one-shot entry points → 114 distinct sounds and variants: 187 files, counting takes and wet.
  - 9 `Sound` continuous layers: 11 files (`air` and `drag` also wet).
  - 10 emitter kinds: 14 files.
  - The voice chime, 8 crackle beds and 7 impulses (the depot and 6 voice rooms).
- **Runtime only:**
  - voice placeholder murmur (random, shaped to each line; until recordings exist);
  - radio static swell (automation spans the voice's length);
  - `setEnabled` (mixer);
  - `Music` (already files).

## Open questions for the audio port

1. **The reverb.** There are two choices:
   - **Baked `_wet` files.** These are exact, but every scene gets the same depot room.
   - **Dry files plus a send.** This lets the room vary per scene. But Unity's built-in SFX Reverb only approximates a
     2.4 s noise impulse, and an exact match needs a convolution reverb (a native plugin, or a package such as Steam
     Audio). The impulses are in `ir/`.
2. **The voice chain in Unity.**
   - The tanh waveshaper (drive 1.3–3), the amplitude-modulation "ring" and the detune wow and flutter have no built-in
     mixer effects. Unity's Distortion effect uses a different curve.
   - Each needs a small DSP script (`OnAudioFilterRead`) or a native audio plugin. Wow and flutter can be done as
     AudioSource pitch modulation.
3. **The voice placeholders.** Until the director's recordings exist, should Unity play the murmur, which needs a
   runtime synth or one render per voice id, or subtitles only?
4. **Panning.** The web build pans nothing. Should positional sources in Unity stay centred (spatial blend for
   attenuation only), or pan as a design improvement?
5. **Variety.** The web build re-randomizes every play (pitch, timing). The takes here are fixed (3–4). Footsteps,
   gate ticks and drips may want more takes, or a small random pitch (about ±10 %, the code's spread).
6. **The shared hiss.** The `hiss` loop is shared by the DL-01 steam and the White's warning `hiss(1)`. The steam
   sets it every frame (`updateAtmosphere`, 7965), so the warning's level is overwritten on the next frame and in
   practice is never heard. This looks like a latent web-build bug. Should Unity give the White its own hiss source
   (`loop_hiss` at 1 for 0.9 s), as the code intends?
7. **Unused music files.** Ten files in `assets/music/` aren't referenced (listed above): confirm they can be left out.
