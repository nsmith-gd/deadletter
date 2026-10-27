# Audio map for the Unity port

**Status:** 26 October 2026, issue #13 (U-16). This is the issue's acceptance list: every cue in `docs/audio_audit.md`
mapped to its clip (an `SfxBank` key or a music key) and to the call that plays it in Unity.

**Sources:** the sounds are described in `docs/unity/audio_inventory.md`, and the design is
`docs/unity/port_architecture.md` §4.23–4.25. Line numbers are `game/undelivered/index.html`'s.

## Decisions

| Question | Decision | Where |
|---|---|---|
| Unity audio or FMOD | **Unity's AudioMixer**, the issue's default. No FMOD package; the director can still choose FMOD. | — |
| Reverb | **Baked.** The `_wet` renders ship, and there is no runtime convolution. The dry files and `ir/` stay in `art/sfx/out/` as sources. | `SfxCatalog.FromFiles(…, WetPolicy.PreferWet)` |
| Voices | **Placeholders, no voice DSP.** You get subtitles, the treatment's crackle bed and the tannoy chime. A recording plays once one is imported. When recordings arrive, bake the chain offline. | `VoicePlayer`, `VoiceRules` |
| Panning | **On-screen x, ±0.4 at the frame edges**, linear between, held at the edge off-screen. One setting: `AudioWorld.edgePan`. | `PanLaw`, `AudioWorld.PanFor` |
| The White's hiss | **Audible.** It gets its own layer, so the DL-01 steam can't overwrite it (port_architecture §9 #16). | `SfxLoop.WhiteHiss`, `SfxPlayer.WhiteWarning()` |
| Unused music | The 10 unreferenced files are **not imported**. | `MusicCatalog.Unreferenced` |
| One copy in git | `Dead Letter → Audio → Import Audio` copies the WAVs and the 19 used music files into `Assets/Audio/` (gitignored). It writes their `.meta` files with **stable GUIDs** (MD5 of the asset path) and builds `Assets/Audio/SfxBank.asset`. | `AudioImporter`, `StableGuid`, `Assets/Audio/.gitignore` |
| Import settings | **Music:** Vorbis 0.7, compressed in memory (not streamed, so `PlayScheduled` is sample-exact for the moments). **Loops and voice:** Vorbis 0.6. **Short SFX:** ADPCM, decompressed on load. **Switch:** music Vorbis 0.5, loops 0.45, set through the `"Switch"` platform string. | `AudioImportSettings` |
| Music loops | The importer trims each loop to its loop region (the 2 s padding goes), so loops are native to the clip. | `AudioImporter.TrimLoop` |

## How a sound is played

| Kind | Core (decides) | Runtime (plays) |
|---|---|---|
| One-shot SFX | `SfxKeys` (the prototype's name → key), `SfxPicker` (seeded, no take twice in a row), `PanLaw` | `SfxPlayer.Play(key, volume[, worldPos])`, pooled 2D sources → **SFX** |
| Continuous layers | `SfxLoopMixer` (level → volume with each layer's τ), `AtmosphereRules` | `SfxPlayer.SetLoop(SfxLoop.X, level)`, `SfxPlayer.WhiteWarning()` |
| Emitters | `EmitterState` (region, deck, condition, level·k², glides, blips, free after 3 s), `PrologueEmitters` | `AmbientEmitter` (one per emitter; `Configure(PrologueEmitters.All[i], …)`) → **Ambience** |
| Music | `MusicDirectorModel` (cue, queue, handovers, ambience, fades, bus), `AmbienceRules`, `MusicCues` | `MusicDirector` (cue A/B and ambience A/B, `PlayScheduled` on `AudioDspMusicClock`) → **Music** |
| Moments | `MomentDirector`/`CueClock` (U-13) + `MusicDirectorModel.Moment` | `DirectedMomentPlayer.Trigger(name)` → `MusicDirector.StartMoment` |
| Voices and tannoys | `VoiceRules` (one at a time, chime lead, subtitles, end, positional fade, duck), `TannoyRules`, `VoiceCardAct`, `VoiceCatalog` | `VoicePlayer` (tannoys run on their own from `AudioWorld`; cards: `PlayCard(id)`; others: `Play(id, options)`) → **Voice** |

**Status legend**
- **Auto:** plays from Core's tables once `AudioWorld` has his x, region, deck and the named condition. No scene code is needed.
- **Ready:** the clip, the Core rule and the Runtime call all exist. The scene port (U-20 to U-22) adds the one call at the line cited.
- **Placeholder:** a voice. The subtitles, crackle bed and chime play; the recording is missing (`docs/voice_script.md`).
- **Gap:** in the audit but not in the web build, so there's no render. It's the director's call (questions below).

## The audit, scene by scene

### Three new systems

| Audit item | Clip | Trigger in Unity | Status |
|---|---|---|---|
| Emitters (positional loops mixed by distance) | `amb_*` (see each scene) | `AmbientEmitter` + `EmitterState.Update` (L1196–L1209) | Auto |
| Voice-card player (crank, then the recording) | `mech_ratchet` at 0.25 and 0.7 s; the voice at 1.2 s (loose card: `d17_tap`, voice at 0.9 s); `curio_found` the first time | scene's card act → `SfxPlayer.Play` at `VoiceCardAct` times → `VoicePlayer.PlayCard(id)` (L6656–L6677) | Ready |
| Tannoys (once as he passes; again fainter after 150 s away) | per voice id | `VoicePlayer` → `TannoyRules.Update` (L6679–L6692) | Auto (Placeholder voices) |
| Old-recording chain | `voice_crackle_<treatment>`, `voice_tannoy_chime` | `VoicePlayer` (no DSP; decision above) | Placeholder |

### DL-01 The Wake

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: relay pulse | `mech_relay_0/1/2` (+wet); opening uses the same | every 6 s: `SfxPlayer.Play(SfxKeys.Relay(i), strength)` at 0, 0.5, 1.0 s (L8515); opening frames 120–360 (L1583–L1589) | Ready |
| Has: hum | `loop_hum` | `SfxPlayer.SetLoop(SfxLoop.Hum, level)`: opening 0.25/0.5/1 (L1582–L1584), play 1 (L8104) | Ready |
| Has: sparks | `mech_spark` (3 takes) | `SfxPlayer.Play(SfxKeys.Simple["spark"])` (L1584, L1586, L4513) | Ready |
| Has: crank ratchet | `mech_ratchet`, `mech_door_rumble`, `mech_door_open` | each stroke (L1889); open (L1890) | Ready |
| Has: shutter | `mech_rattle_900`, `mech_clank`, `mech_chain_550`, then `mech_thud` at 560 ms | shutter release (L1678–L1679) | Ready |
| Has: cart | `mech_thud` | cart into the trench (L4757) | Ready |
| E: drip from the burst pipe by the trench | `amb_drip` (3 takes) | `PrologueEmitters.All[1]` (x 7.3, 0.7, reach 4.5). The atmosphere's falling drops: `env_drip` at v = 1 − dist/6 (L7904) | Auto / Ready |
| E: dispatch board tick | `amb_tick` | `PrologueEmitters.All[0]` (x 1.0, period 0.9) | Auto |
| C: cord lamp's chain tinkles as he walks past | — (the cord act has `mech_creak_400` at f > 20, L1873, `mech_lamp_click` + `elec_buzz_short` on, L1867) | cord act calls only | Gap (walk-past tinkle) |
| T `tan_depot_1` | `voice_crackle_tannoy`, `voice_tannoy_chime` | `VoicePlacement` x 1.69, at 8.6 ± 0.6, reach 14, condition `released` | Auto, Placeholder |
| (steam) | `loop_hiss` | `SfxPlayer.SetLoop(SfxLoop.Hiss, AtmosphereRules.SteamHiss(x, inPlay, HissLevel(puffing)))` (L7965) | Ready |
| (distant machinery) | `env_distant` (60 %) or `env_groan` | `AtmosphereRules.Update(t, inPlay, voicesHeld)` every 6–14 s (L7964) | Ready |
| (opening and play voices) | `dispatch_wake` (frame 204, L1586), `dispatch_item` (start of play, L8109) | `VoicePlayer.Play(id, VoicePlayOptions.Flat(0.8))` | Placeholder |

### DL-02 The Sorting Hall

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: tube cough | `mech_chain_300`, `d17_tap` at 200 ms | the tube letter (L4772) | Ready |
| Has: letters | `d17_tap` (pick-up, L4473); `d17_knock` + `d17_chirp` at 250 ms (posted, L4486); `mech_servo_350_900_1500` (close-up scan, L3951) | `SfxPlayer.Play` | Ready |
| Has: franker | `curio_stamp` (+wet) at curio frame 30; franking press `mech_clank` + `mech_thud` (L7350) | curio clip cue / press | Ready |
| Has: mugs | `curio_mug` (+wet) f26, `curio_mug_down` f76 | curio clip cues (L5104–L5118) | Ready |
| E: the stopped fan's loose blade | `amb_fan` (3 takes) | `PrologueEmitters.All[2]` (x 19.8) | Auto |
| E: fluorescent buzz under the gantry | `amb_buzz_loop` | `PrologueEmitters.All[3]` (x 23.4) | Auto |
| I: pigeonhole wall rattles letters when brushed | — | — | Gap |
| I: a letter dropping into a slot (hollow paper) | `d17_knock` + `d17_chirp` (the posting sound) | posting (L4486) | Ready (no paper sound of its own: Gap) |
| V `card_sorter` | `voice_crackle_card` | `VoicePlayer.PlayCard("card_sorter")` from the card act (stand x 16.45) | Placeholder |

### DL-03 The Weight of the Job

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| E: the gate's counterweight chain creaking while part-open | — (winding plays `mech_gate_tick` every 5 cm, L2382; the drop `mech_gate_slam`, L2386) | gate rule calls only | Gap |
| C: the dial's needle ticking as the load changes ("raise it") | `mech_tick` | each 20° detent (L4906); raise the per-call volume in the scene port | Ready |
| (plate, weight, trolley) | `mech_plate` (L2375), `d17_lift` (L2277), `mech_scrape` (L2278), `d17_setdown_*` (L2285), `loop_roll` (L2370), `mech_squeak` (L2350) | `SfxPlayer.Play` / `SetLoop(SfxLoop.Roll, …)` | Ready |

### DL-04 The Racks

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: tubes | `loop_tubes` | `SetLoop(SfxLoop.Tubes, lit·max(0.25, 1 − \|x − 34\|/8))` (L2428) | Ready |
| Has: the row lights' cascade | `mech_row_on_0..5` (+wet) | `SfxKeys.RowOn(i)` at 1.0, 2.2, 3.4, 4.6, 5.8, 7.0 s (L2422) | Ready |
| Has: the lament | music `racks` | `MusicDirector.Play("racks", 0.6)` at the reveal (L2403) | Ready |
| E: a rack lamp's failing starter | `amb_buzz_loop` | `PrologueEmitters.All[4]` (x 36, condition `revealed`) | Auto |
| E: the bay's cradle servo idling | — (the cradle plays `mech_servo_500_260_520` / `_600_300_700` when it moves, L4790, L4805) | cradle rule calls only | Gap (idle) |
| T `tan_racks` | tannoy crackle + chime | `VoicePlacement` x 38.2 ± 3.0, condition `revealed` | Auto, Placeholder |
| (the grief moment) | music `kin` | `DirectedMomentPlayer.Trigger("kin")` (L1958) | Ready |

### DL-05 The Ration Hall

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| E: a dripping tap behind the counter | `amb_drip` | `PrologueEmitters.All[5]` (x 56.2) | Auto |
| E: the shrine's candle flames guttering | — | — | Gap |
| T `tan_rations` | tannoy crackle + chime | `VoicePlacement` x 56.6 ± 2.6 | Auto, Placeholder |
| V `card_queue` (loose card) | `voice_crackle_card_worn` | `VoicePlayer.PlayCard("card_queue")` (tap, voice at 0.9 s) | Placeholder |
| (weigh-in) | `mech_tick` (dial), `mech_click`, `elec_buzz_short`, `mech_clank` + `mech_alarm_bell` (over), `mech_ratchet`, `mech_chain_1500`, `mech_clunk` | L4897–L4917 | Ready |

### DL-06 Return to Sender

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: belt | `loop_belt`, `mech_klaxon`, `mech_belt_stop` | `SetLoop(SfxLoop.Belt, …)` (L2830), klaxon (L2822, L2932), stop (L2932) | Ready |
| Has: scanner | `mech_scan_sweep` (L2792), `mech_answer_0..2` (L2797), `mech_reject` (L2801), `d17_chirp` (L2800) | `SfxPlayer.Play` | Ready |
| Has: carriers | `mech_hatch_lift`, `mech_bell` (dock), `mech_clack`, `mech_clunk`, `loop_roll` 0.7 while riding (L2969) | L2680–L2739 | Ready |
| E: the scanner's mains hum | `amb_hum_loop` | `PrologueEmitters.All[6]` (x 61.9, lower deck) | Auto |
| I: the scanner's speaker, "Return to sender" | machine crackle | `VoicePlayer.Play("tan_scanner", VoicePlayOptions.At(61.9, 6, 0.8))` 350 ms after the reject (L2801), with `MusicDirector.Play("dead", 0.15)` | Placeholder |
| V `card_reader` (secret room, the one who stayed) | elder crackle | `VoicePlayer.Play("card_reader", VoicePlayOptions.Flat())` on entering (L6497) | Placeholder |

### DL-07 The Heap

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: heap slides | `mech_scrape` (L4953), `d17_land` 0.6 (L4508), `d17_worried` (L2981), `mech_thud` + `mech_tumble` (L2993) | `SfxPlayer.Play` | Ready |
| Has: the clock | `mech_tick` once a second near it, upper deck (L6795); `curio_wind` f12 | `SfxPlayer.Play` | Ready |
| E: paper shifting in the heap | — (the placed emitter is the heap's water, `amb_lap_loop`, `PrologueEmitters.All[7]`) | — | Gap |
| V `card_heap` | card crackle | `VoicePlayer.PlayCard("card_heap")` (x 68.0, lower deck) | Placeholder |

### DL-08 The Handbrake

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: lift crash | `mech_lift_crash` at volume v | `SfxKeys.LiftCrash(v)`, `LiftCrashVolume(v)` (L3193) | Ready |
| Has: pawl | `mech_pawl_click` + music `latch` (L3125), `mech_pawl_clatter` (L3316–L3317) | `SfxPlayer.Play`; `MusicDirector.Play("latch", 0.15)` | Ready |
| Has: the White's water | `env_splash` (L7152–L7172), `death_grabbed`, the warning `loop_hiss` on its own layer | `SfxPlayer.Play`, `SfxPlayer.WhiteWarning()` | Ready (hiss fixed) |
| E: the sump's water lapping | `amb_lap_loop` | `PrologueEmitters.All[8]` (shaft middle, x 87.05, reach 4.5) | Auto |
| E: the goods lift's snapped cable swinging | — | — | Gap |
| C: a suitcase creaks as he passes | — | — | Gap |
| (platform) | `mech_gate_tick` (L3186), `loop_drum` (L3200), `mech_clunk` (L3188), `mech_alarm_bell` ×3 + `mech_klaxon` at 2.7 s (L3224–L3225), `mech_crate_land` at v (L3157) | `SfxPlayer` | Ready |

### DL-09 The Slipping Cage

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: the cage | `mech_lurch`, `mech_lift_crash_v040`, `mech_chain_1200/2500`, `mech_alarm_bell`, `env_groan`, `mech_creak_800`; music loop `failure` | L5022–L5049; `AmbienceRules` (`CageDanger`) | Ready |
| Has: hopscotch | `d17_step` at 0.9 (L3356, L3372), `d17_chirp`/`d17_worried`/`d17_tap`/`d17_strain` (L3406) | `SfxPlayer.Play` | Ready |
| Has: the coin viewer | `curio_coin` f58 | curio clip cue | Ready |
| E: the den's music box, the cue to the vent | `amb_musicbox_loop` (a loop of one turn of the tune) | `PrologueEmitters.All[9]` (x 107.17, reach 3.2) | Auto |
| E: wind on the balcony | `amb_wind_loop` | `PrologueEmitters.All[10]` (x 114.5) | Auto |
| I: Use the music box in the den to wind it | — | — | Gap |
| V `card_den` (three children) | child crackle; recordings `card_den_1..3` in turn | `VoicePlayer.Play("card_den", VoicePlayOptions.Flat())` (L6502) | Placeholder |
| T `tan_bridge` | tannoy crackle + chime | `VoicePlacement` x 116.1 ± 2.4, reach 7 | Auto, Placeholder |
| (the city) | music `refuge`, then the `order` loop | `DirectedMomentPlayer.Trigger("refuge")` (L3433); `AmbienceRules` (`Awed`) | Ready |

### DL-10 Up Only

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: the lift and its gauge | `mech_chain_2000`, `mech_clunk`, `mech_squeak`, `mech_click` (UP), `elec_buzz_short` (refused), `mech_creak_500`, `mech_gate_slam` | L4583–L4637 | Ready |
| T `tan_relocation` (loudest and clearest) | tannoy crackle + chime | `VoicePlacement` x 120.45 ± 2.2 | Auto, Placeholder |
| V `card_lastcar` (loose) | card crackle | `VoicePlayer.PlayCard("card_lastcar")` (stand x 122.25) | Placeholder |
| (ring C) | music `ringc`; `heaps` × 0.6 while riding | `DirectedMomentPlayer.Trigger("ringc")` (L4588); `AmbienceRules` (`RidingUpOnly`) | Ready |

### DL-11 The Child at the Address

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| Has: radio | `curio_radio` (+wet) f34, then `radio_above` | curio cue; `VoicePlayer.Play("radio_above", VoicePlayOptions.Flat(0.9))` (L6724) | Ready / Placeholder |
| Has: switch | `curio_switch` f16 | curio cue | Ready |
| Has: doorbell | `mech_alarm_bell` every 0.55 s while it rings | L7257 | Ready |
| Has: knock | `d17_knock` | C-114's door (L3651–L3652) | Ready |
| Has: the White | `env_splash`, `loop_hiss` warning (own layer), `death_grabbed` | `SfxPlayer` | Ready |
| E: water lapping along the flooded lane | `amb_lap_loop` | `PrologueEmitters.All[11]` (x 148.3), `[12]` (x 150) | Auto |
| E: the well's wind at the ending landing | `amb_wind_loop` | `PrologueEmitters.All[14]` (x 174.5) | Auto |
| E: the splice box's new hum (heard before the look up) | `amb_hum_loop` | `PrologueEmitters.All[13]` (x 170.85) | Auto |
| I: the radio finds a voice from far above | `radio_above` (radio treatment; the static swell is runtime-only and not built) | as Has: radio | Placeholder |
| V `card_mara_parent` | card crackle | `VoicePlayer.PlayCard("card_mara_parent")` (x 158.07) | Placeholder |
| (the desk's marks, the window, the end) | music `childP` (L3547), `window` (L2105), `end` (L8188) | `MusicDirector.Play("childP")`; `DirectedMomentPlayer.Trigger("window")`; `MusicCues.Finish` | Ready |

### Chapter 1 Attendance

| Audit item | Clip | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| DL-12 T `att_gate_1` to `att_gate_3` (the register) | tannoy crackle + chime | `VoicePlayer.Play(id, VoicePlayOptions.Flat(0.8))` (L5391, L5393) | Placeholder |
| DL-12 V `att_caretaker` (lost property) | elder crackle | `VoicePlayer.Play("att_caretaker", Flat())` (L6506) | Placeholder |
| DL-13 the lesson `att_lesson`, sticking when braked | card crackle | `VoicePlayer.Play("att_lesson", At(speakerX, 11, 0.75))` (L5421); braked: `StickAt = 9.2`, level 0.7, reach 10 (L5358). A placeholder can't stick: that needs the recording. | Placeholder |
| DL-13 E the apparatus's clockwork | `amb_tick` (period 0.25), `amb_machine_loop` | `PrologueEmitters.All[16]`, `[17]` (condition `lessonRunning`) | Auto |
| DL-14 E the blinds' chain over its pulleys | `mech_chain_2200` when the blinds move (L5372, L6092); not an emitter | `SfxPlayer.Play(SfxKeys.Chain(2.2))` | Ready (as a one-shot) |
| DL-14 V `att_teacher` (stock cupboard) | card crackle | `VoicePlayer.Play("att_teacher", Flat())` (L6510) | Placeholder |
| (school tubes) | `amb_buzz_loop` | `PrologueEmitters.All[15]`, `[18]` | Auto |
| (rest hour, the bell, the trolley, the volunteer) | `att_rest`, `att_bell` (tannoys, conditions `restDoorShut`, `dismissed`), `att_trolley` (L6400), `att_volunteer` (card x 332) | `VoicePlayer` | Auto / Placeholder |
| (bed, child, endAtt) | music `bed` (L8092, L5765), `child` (L5474, L5734), `endAtt` | `MusicDirector.Bed(on)`, `Play("child", 2.5 / 3)`, `MusicCues.Finish(…, chapterOne: true)` | Ready |

## Music

| Key | Clip (`Assets/Audio/Music/`) | Trigger in Unity (prototype line) | Status |
|---|---|---|---|
| wake | `prologue_cue_wake.mp3` | `MusicDirector.Play("wake", 0.6)` after the intertitle (L8068). Handover to `lower_works` at 48 s. | Ready |
| hall | `prologue_cue_hall.mp3` | `Play("hall")` at x > 7.5 before the bulkhead opens (L2066) | Ready |
| threshold | `prologue_cue_threshold.mp3` | `Play("threshold")` when the bulkhead is open (L1890) | Ready |
| racks | `prologue_cue_racks.mp3` | `Play("racks", 0.6)` (L2403) | Ready |
| kin, refuge, ringc, window | `prologue_cue_<key>.mp3` | `DirectedMomentPlayer.Trigger(key)` → `MusicDirector.StartMoment` (L1958, L3433, L4588, L2105) | Ready |
| dead | `prologue_cue_dead.mp3` | `Play("dead", 0.15)` (L2801) | Ready |
| latch | `prologue_cue_latch.mp3` | `Play("latch", 0.15)` (L3125) | Ready |
| childP | `prologue_cue_child.mp3` | `Play("childP")` (L3547) | Ready |
| end / endAtt | `prologue_cue_end.mp3` / `dl01_end.mp3` | `MusicCues.Finish(model, now, chapterOne)` (L8186–L8189) | Ready |
| child | `dl05_child.mp3` | `Bed(false)` + `Play("child", 2.5)` (L5474), `3` (L5734) | Ready |
| lower_works, order, heaps, failure | `prologue_loop_<key>_loop.wav` (trimmed 2–34 s) | `AmbienceRules.Apply(model, context, now)` every frame in play (L8163) | Ready |
| bed | `dl01_bed_loop.wav` (trimmed 2–50 s) | `MusicDirector.Bed(true/false)` (L8092, L5734, L5760, L5765); the rack's hush `Stop(5)` (L5760) | Ready |
| pause, duck | — | `MusicDirector.SetPaused` (L8126, L8132); the voice duck is automatic (`VoicePlayer` → `Duck`) | Ready |

## All SFX keys

Every `Sound.*` call has a key: `SfxKeys.Simple[name]`, or a function for calls with an argument that picks the file
(`Relay(i)`, `Answer(i)`, `RowOn(i)`, `Creak(s)`, `Chain(s)`, `Rattle(s)`, `Servo(s, f0, f1)`, `SetDown(onDeck)`,
`LiftCrash(v)`, `Curio(kind)`, `Death(how)`). An argument that is a level (`crackle(v)`, `drip(v)`, `splash(v)`, `zap(v)`,
`clack(v)`, `gateSlam(v)`, `crateLand(v)`, `land(v)`, `step(soft)`, `relay(i, strength)`) is the `volume` of
`SfxPlayer.Play`. `AudioRulesTests.Catalog_CoversEveryCallTheGameMakes` checks that every key has a render. The trigger
lines for each are in `docs/unity/audio_inventory.md`.

The randomized sounds have 2–4 fixed takes. In the bank only take 1 has a `_wet` file, so with `PreferWet` the other takes
play dry (see the questions).

## Director, on first open

1. **Import.** Run **Dead Letter → Audio → Import Audio**, then check the Console:
   - `Import done: … bank Assets/Audio/SfxBank.asset has 143 sounds and 19 music clips`;
   - no `GetData failed` errors (if there is one, a loop wasn't trimmed).
2. **Make the mixer by hand.** Unity has no public API to build an AudioMixer, so there is no builder.
   1. In the Project window, right-click `Assets/Audio` → **Create → Audio Mixer**. Name it `DeadLetter`.
   2. Open **Window → Audio → Audio Mixer**. Select `Master`. In **Groups**, press **+** four times to add `Music`,
      `SFX`, `Voice` and `Ambience`, all children of `Master`.
   3. Set the faders: `Master` **−1.9 dB** (the web build's 0.8), `Ambience` **−0.9 dB** (0.9), and the others **0 dB**.
   4. On `Music`: **Add Effect → Compressor**. Set Threshold **−24 dB**, Attack **250 ms**, Release **1200 ms** and Make-up
      **0 dB**. Unity's Compressor has no fields for the web build's ratio (4) and knee (12 dB), so check by ear at
      the refuge cue that it no longer swells past the rest.
   5. Optional, for the options' sound toggle: right-click `Master`'s Volume → **Expose**, and rename the parameter
      `MasterVolume`.
3. **Set up `DL_Persistent`.** Add these, with the mixer groups assigned:
   - `AudioWorld`: `listener` = D-17's root. Leave `edgePan` at 0.4 unless the pan is too wide or too narrow.
   - `SfxPlayer`: `bank` = `SfxBank`, `sfxGroup` = SFX.
   - `MusicDirector`: `bank`, `musicClock` = the `AudioDspMusicClock` from U-13, `musicGroup` = Music.
   - `VoicePlayer`: `bank`, `voiceGroup` = Voice, `music` = the MusicDirector, `moments` = the `DirectedMomentPlayer`.
   - On `DirectedMomentPlayer`: `score` = the MusicDirector and `voices` = the VoicePlayer. Its per-moment cue sources are
     then unused.
   - Emitters: one `AmbientEmitter` per `PrologueEmitters` row (`ambienceGroup` = Ambience). The scene builders will spawn
     these later.
4. **Commit.** Commit `DeadLetter.mixer`, `Assets/Audio/SfxBank.asset` and the folder metas. The audio files and their
   `.meta` files stay ignored: the importer writes the metas with stable GUIDs (MD5 of the path), so they come out
   identical on every machine and SfxBank's references hold. On a fresh clone, run the importer before opening scenes.
5. **Listen.** Check these against the web build (`game/undelivered/index.html`):
   - the wake's handover to `lower_works` at 48 s;
   - the racks cue hiding the loop over 4 s;
   - a tannoy's chime and subtitles in DL-01;
   - the White's hiss in DL-08 (new: it was silent on the web);
   - footsteps varying without repeats;
   - pan staying gentle at the frame edges.

## Questions for the director

1. **Wet takes.** Only `_v1` of a randomized sound has a `_wet` file. With the reverb baked, takes 2–4 play dry, which is
   audible on sparks, drips, zaps and deaths. Should those takes be re-rendered wet (cheap with `tools/audio_render`), or
   should only the wet take play?
2. **Voice placeholders.** Today a voice is its crackle bed (plus the chime) and subtitles; there is no murmur. Should a
   murmur be rendered per treatment (`voice_placeholder_<treatment>`, which `VoicePlayer` already plays if present), or
   should we wait for recordings?
3. **MP3 priming.** The web build measured `PRIME = 0` in Chrome. Unity's decoder may treat the MP3 encoder delay
   differently (about 25 ms), which would shift the moments' cue clock and the trimmed loop points. Measure once on a
   moment with a clap test, or re-export the music as WAV/OGG?
4. **Mixer snapshots per region.** The issue mentions them, but the web build has no per-region mix beyond the ambience
   map. Should we add snapshots, and if so what should change between regions?
5. **The audit's gaps.** These were planned but never built:
   - the cord chain's walk-past tinkle;
   - the pigeonholes;
   - the counterweight chain;
   - the rack starter's clicks;
   - the cradle's idle servo;
   - the candles;
   - the heap's paper;
   - the snapped cable;
   - the suitcase;
   - winding the den's music box.

   Should these be built now (new renders), or left as they are in the web build?
