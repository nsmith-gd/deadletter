# Accessibility: photosensitivity check of flashing effects

Issue #29 (U-17b), as asked for in `port_architecture.md` §4.29. This file lists every flashing or flickering effect in the
prologue (DL-01 to DL-11) and chapter 1 (DL-12 to DL-17). For each one it gives the prototype lines (`game/undelivered/index.html`),
the flash rate and the size of each change, with calm mode ("Reduce flicker and flashes", `Settings.Calm`) off and on.

The limits and the catalogue are Core data:

- `Core/Presentation/FlashSafety.cs` holds the limits and a counter that measures a sampled intensity curve against them.
- `Core/Presentation/FlashEffects.cs` holds one `FlashEffect` per row below, with its curve, its area estimate and its source lines.
- `core-tests/FlashSafetyTests.cs` samples every curve at 60, 120 and 240 Hz. It fails if any effect breaks the limit in calm
  mode, or if the set of effects that fail with calm off differs from the list in this file.

## Limits

These are WCAG 2.x SC 2.3.1 (Three Flashes or Below Threshold). ITU-R BT.1702 and Ofcom's guidance use the same three-per-second rule.

| Limit | Value | Core |
|---|---|---|
| Flashes in any 1 s window (window inclusive) | no more than 3 | `FlashSafety.MaxFlashesPerSecond`, `Window` |
| A flash | a pair of opposing changes, each ≥ 10 % of the maximum relative luminance, with the darker state below 0.80 | `LuminanceStep`, `DarkerBelow` |
| Area exemption (general and red thresholds) | a combined flashing area under 25 % of the 10° field, which is 341 × 256 px at 1024 × 768. That is 21,824 px², about **2.8 % of the screen** | `SmallAreaFraction` |
| Red flash (saturated red sources) | R / (R + G + B) ≥ 0.8; any pair of opposing transitions into or out of the red counts, with no darker-state condition, against the same area threshold | `IsSaturatedRed`, `Count(…, red: true)`, `Passes(samples, rate, colour, area)` |

**How the counter works.** It normalises each curve to its own peak and treats that as relative luminance. A transition counts
once the level has moved 10 % away from the last extreme in the opposite direction, and only when the dark side of the
transition is below 0.80. Flashes per second is the most transitions in any 1 s window, divided by 2.

**The red flash rule.** A source whose colour is saturated red (`FlashEffect.Colour`, `FlashEffect.Red`) is counted a second
time with `red: true`: every registered transition counts, bright or dark, so a flicker between 85 % and 100 % of a red lamp is
a red flash even though it is no general flash. The 10 % hysteresis still decides what registers as a transition (otherwise any
noise would count). Only the DL-02 press lamp (`EMIT.PressLamp`, 0.88) is saturated red; Pips' `RED` (0.77) is not.

**Combined area.** WCAG judges the area of everything flashing together, not each effect alone. `FlashEffects.Assess` gives
each effect a scene (`FlashEffect.Scene`, by default the id's prefix, `dl04`) and sums the screen share of every effect in that
scene that is over the limit, under either rule. This is conservative: it treats everything fast in one scene as on screen
together and in phase, whenever in the scene it plays (for example the opening's work bulb and the live cable). An effect that
can play anywhere (the death, the glints, Pips, the service-line relays: scene `*`) is summed with every scene and is judged by
its worst one. A fast effect passes only when that sum is under 2.8 %.

**Why the counts are conservative.** On screen the luminance change is smaller than the counter assumes. Ambient light, fog,
tone mapping, light falloff and the dark palette all dilute it. The bloom strength is 0.55, or 0.35 in calm (`Settings.Bloom`).

**Frame rates.** Each effect is measured at 60, 120 and 240 Hz, and at the worst trigger phase where a trigger can land anywhere
against the clock its flicker runs on (`FlashEffect.PhaseSpan`).

**Area estimates.** The camera uses a 35 mm lens (`hfov` ≈ 54°). The frame is about 5–10 m wide at the volumes in §4.17, for
example DL-01's hall at 9.2 m and the Ration Hall at 6.4 m.

- **Emissive lamps** (bulbs and indicator lamps) and spark particles cover a few to a few hundred pixels, under 1 %, even with
  bloom. Even in the opening's chest close-up (a frame about 1.1 m wide), a 5 cm lamp is about 50 px across.
- **Real lights** change the surfaces in their range. The estimates take the lit patch at that framing:
  - 2–4 m ranges give 5–15 %.
  - Room fills, the rack lights and the opening's work spot give 30–60 %.
  - Any real light is therefore treated as above the 2.8 % threshold.

## Table

Abbreviations:

- **F/s**: the worst flashes in any second from the measurement (`FlashEffect.Measure`, the worst of 60, 120 and 240 Hz).
- **Step**: the largest qualifying change as a fraction of the peak.
- **Area**: the share of the screen.

**Result** is calm off, then calm on: pass, fail, or n/a for something with no luminance change. A fast effect under the area
threshold passes with calm off on area alone, and only when its combined area (above) is under 2.8 %. It is marked "pass (area)".

| Effect (Core id) | Source lines | Rate from the code | F/s off | Step off | Area | Calm off | Calm on (F/s) | Action |
|---|---|---|---|---|---|---|---|---|
| Opening parcel lamp (`dl01.openingParcelLamp`) | L1552–L1553, `flicker` L1528 | 6 steps in 19 frames at 24 fps, once | 2.5 | 0.85 | <1 % | pass | pass (0.5, 20-frame ramp) | none |
| Opening work bulb, spot 24 (`dl01.openingWorkBulb`) | L1569–L1572 | 7 changes in 24 frames (1.0 s), once at f226 | 3.5 | 1.0 | ~60 % (close-up) | **fail** | pass (0.5, ramp) | warning (once, at boot) |
| Opening eyes (`dl01.openingEyes`) | L1575–L1577 | 5 changes in 14 frames, once | 2.5 | 1.0 | <1 % | pass | pass (0.5) | none |
| Opening sparks, spark light 5 (`dl01.openingSparks`) | L333, L1565–L1567 | 2-frame flashes at f150, f153 and f196 | 2 | 1.0 | ~15 % | pass | pass (0, off) | none |
| DL-01 relay pulse, `5·min(1.4, Σ)` (`dl01.relay`) | L332, L1534–L1548, L1567 | sets at 5, 7 and 14 s, then one 1.7 s pulse every 6 s (0.17 Hz) | 1 | 0.71 | ~30 % | pass | pass (1, sine bumps L1543) | none |
| DL-01 live cable (`dl01.cable`) | L7938–L7941 | `sin 90t` square (14.3 Hz) 2.5↔0.75 for 0.18 s, every 3–8 s | 3–4 (by phase and frame rate) | 1.0 | ~15 % | **fail** | pass (1, steady 0.4) | warning |
| DL-01 cord lamp (`dl01.cordLamp`) | L7948–L7950 | `sin 70t` (11 Hz) for the first 0.4 s after a pull | 4.5 | 0.84 | ~15 % | **fail** | pass (0, steady) | warning; not lit in the port yet (`LightDriver.Off`) |
| DL-01 crank lamp (`dl01.crank`) | L7962 | 0.27 Hz, ±10 % | 0 | — | ~20 % | pass | pass (0) | none |
| DL-02 press lamp, red (`dl02.pressLamp`) | L7347, `EMIT.PressLamp` L483 | `sin 25t` (4 Hz) for the 0.5 s tell, every 2.6 s; saturated red (0.88), so the red flash rule applies too (also 3) | 3 | 1.0 | <1 % | pass (at the limit) | pass (1, held at 2) | none |
| DL-04 row lamps (`dl04.rowLamps`) | L2414–L2422 | `sin 57k` (9.1 Hz) for 0.6 s per row, 6 rows 1.2 s apart | 5.5 | 0.9 | ~15 % | **fail** | pass (0.5, eased L2421) | warning |
| DL-04 rack lights, `0.1 + 3.6·lit` (`dl04.rackLights`) | L2414–L2426 | the mean of the rows | 5.5 | 0.16 | ~40 % (reveal pan) | **fail** | pass (0.5) | warning |
| DL-04 cradle seated lamps (`dl04.cradleLamps`) | L4818–L4820 | `sin 31t` (4.9 Hz) for 2.2 s after seating; **not gated by calm in the prototype** | 5.5 | 0.92 | <1 % (combined with the row lamps and rack lights: ~56 %) | **fail** | pass (0.5) | **new calm curve**: `Cradle.SeatedLamp(t, calm)` eases to 0.55; bound to the `SeatedLamps` node (see below) |
| DL-05 Ration strip, spot 14 + fill 2.2 (`dl05.rationStrip`) | L4927–L4929 | stutter `sin 61t` (9.7 Hz) 0.25↔1 for 1.08 s every 8.98 s; shimmer 0.92±0.08 otherwise | 10 | 0.75 | ~40 % | **fail** | pass (0, steady 1) | warning |
| DL-05 candles (`dl05.candles`) | L4930 | `sin 7.3t · sin 3.1t`: 0.67 and 1.66 Hz beats, ±12 % | 1 | 0.11 | ~4 % | pass | pass (1, unchanged as in the prototype) | none |
| DL-06 scanner, idle (`dl06.scanner`) | L2220, L2429–L2432 | 0.35 Hz sine; 0xff4a2a is not saturated red (0.69) | 1 | 0.1 | ~8 % | pass | pass (1, unchanged) | none |
| DL-06 pit skylight (`dl06.pitSky`) | L2846–L2847 | 0.05 Hz, ±15 % | 0.5 | 0.1 | ~50 % | pass | pass | none |
| Pips reject blink (`pips.reject`) | L6853, L6873–L6883 | `sin 18t` (2.9 Hz) for 1.4 s; RED (1, 0.22, 0.08) is 0.77, just under saturated red (the general rule only); not gated by calm | 3 | 0.95 | <1 % | pass (at the limit) | pass (3, at the limit) | none |
| DL-08 beacon (`dl08.beacon`) | L3230–L3235 | 1.1 Hz sine; the beacon spot (7) sweeps at 0.5 Hz | 1.5 | 0.14 | <1 % (lamp) | pass | pass (0, held at 0.7) | none |
| DL-08 tunnel arc light (`dl08.arcLight`) | L7321–L7325, L7386–L7415 | per-frame random 0.6–1.0 during two 0.45 s live windows every 2.4 s; **calm in the prototype is the same random flicker at 0.6×** | 8 | 1.0 | ~10 % | **fail** | pass (1, steady 0.48) | warning; **calm deviation** (the port's calm holds it steady) |
| DL-09 cage bulb (`dl09.cageBulb`) | L5077 | `sin 37t` (5.9 Hz) during shudder, slip, stall and crash | 6 | 0.9 | <1 % (combined with the dying eye: 1.2 %) | pass (area) | pass (0, held at 3) | none |
| DL-09 tray lamp (`dl09.trayLamp`) | L5073 | 0.8 Hz half-sine | 1 | 0.11 | <1 % | pass | pass | none |
| DL-10 UP lamps buzz (`dl10.upLamps`) | L4660–L4662 | `sin 40t` (6.4 Hz) for 0.9 s per refused press; **not gated by calm** | 6.5 | 0.95 | <1 % (combined with the lobby bulb: ~31 %) | **fail** | pass (0.5, steady 4) | warning; **calm deviation** (spec for U-15) |
| DL-10 Up Only lobby bulb, light 1.4 (`dl10.lobbyBulb`) | L4083, L4663–L4665 | stutter `sin 53t` (8.4 Hz) 0.2↔1 for 1.0 s every 7 s | 9 | 0.8 | ~30 % | **fail** | pass (0, steady) | warning |
| DL-10 ring C moment light (`dl10.ringcLight`) | L4610, L4618–L4621 | 2.5 s ramp up, 1.5 s ramp down | 0.5 | — | ~40 % | pass | pass | none |
| DL-11 lane bulb, light 0.8 (`dl11.laneBulb`) | L3489, L3562–L3568 | ±8 % `sin 47t` (7.5 Hz) shimmer on a 0.64–0.92 sag, plus 4.9 Hz drop-outs to 0.15 for 1.08 s every 9 s | 8 | 0.87 | ~15 % | **fail** | pass (0, steady 1) | warning (the shimmer counts only under the conservative normalisation) |
| DL-11 ring C bell lamp (`dl11.bellLamp`) | L7255–L7258 | `sin 18t` (2.9 Hz) while ringing; amber; not gated by calm | 3 | 0.92 | <1 % | pass (at the limit) | pass (3, at the limit) | none |
| DL-12 gate and coat lamps (`dl12.gateLamps`) | L5395–L5398 | 1.1 Hz square | 1.5 | 0.85 | <1 % | pass | pass (0) | none |
| DL-12 peg lamp while reaching (`dl12.pegReach`) | L5397–L5398 | `sin 14t` (2.2 Hz) for 2.4 s; not gated by calm | 3 (worst phase) | 0.89 | <1 % | pass (at the limit) | pass (3, at the limit) | none |
| DL-14 clutch jam light (`dl14.clutchLight`) | L5221, L5462–L5466 | `sin 31t` (4.9 Hz) through the `dt·10` follow, ±0.15; **not gated by calm** | 5.5 | 0.19 | ~5 % | **fail** | pass (0, steady 0.72) | warning; **calm deviation** (spec for U-15) |
| DL-14 clutch sparks (`dl14.clutchSparks`) | L5457–L5459 | about 14 bursts of 3 particles per second, each fading over 0.4–0.6 s; **not gated by calm** (only the shake at L5461 is) | n/a (moving points) | — | <1 % | pass (area) | — (none in calm) | **calm deviation**: the port bursts no sparks in calm |
| DL-14a window eyes (`dl14a.eyes`) | L6280–L6281 | 1.1 Hz square | 1.5 | 0.8 | <1 % | pass | pass (0) | none |
| DL-16a load lamps (`dl16a.loadFlash`) | L6299–L6300 | `sin 14t` (2.2 Hz) for 2.4 s; not gated by calm | 3 (worst phase) | 0.99 | <1 % | pass (at the limit) | pass (3, at the limit) | none |
| Service-line relays (`att.relays`) | L5160–L5166, L6316–L6325 | 0.25 s every 7 s per lamp; pump blink at 0.95 Hz while refilling | 1.5 | 1.0 | <1 % | pass | pass | none |
| Chapter 2 relay pilots (`ch2.relayPilots`) | none (no prototype): chapter2_plan §4 "The new cable", DL-18 §3 | a 0.3 s sine bump from 0.55 to 1 every 7 s, with the relay's click (`SomeoneHomeLights.PilotLevel`) | 0.14 | 0.45 | ~2 % | pass | pass (0, steady 0.7) | none |
| Glints and prompts pulse (`glints.pulse`) | L7009 | 0.41 Hz, ±15 % | 0.5 | 0.11 | <1 % | pass | pass (0) | none |
| Death: the eye (`death.eye`) | L7445–L7447 | `sin 70t` (11 Hz) for 0.45 s; **not gated by calm** | 4 | 0.9 | <0.3 % (anywhere: its worst scene, DL-01, sums to 75–90 % by frame rate) | **fail** | pass (0.5, fade) | warning; **new calm curve**: `DeathProfile.EyeLevel(t, calm)`; `DeathAct.EyeLevel` reads calm from the graph |
| Death: sparks (`death.sparks`) | L7440, L7448 | one burst, plus shock bursts at 14/s | n/a | — | <1 % | pass (area) | — (gated by calm) | gated in Core as in the prototype: `DeathProfile.SparksFor(calm)`, `SparkRateFor(calm)`, `DeathAct.Sparks` and `SparkRate` (0 in calm) |
| Death: cut to black (`death.cut`) | L7449–L7452, L8100, CSS L107 | one hard cut, then a 1.2 s fade back, once per death | 1 | 1.0 | 100 % | pass | pass | none |
| Directed moments (`kin`, `ringc`, `window`, …) | L3713–L3720, L3745–L3751, L4610–L4621 | camera shots and slow light ramps only; no lightning or flash in any moment | ≤ 0.5 | — | — | pass | pass | none |
| The White | L7040–L7200 | no light effect (the gill emissive is static); its splashes shake the camera | n/a | — | — | n/a | n/a (shake off) | none |
| Camera shake (`camera.shake`) | L3810, L3826–L3831 | a damped tremor: motion, not luminance | n/a | — | — | n/a | off (`CameraRig.Shake`) | none |

The shutter jitter (L1687), the needle and desk wobbles (L2377, L3542, L4738, L4769) and the cable sway (L7267) are motion only.
All of them are already off in calm mode.

## Summary

### Calm mode on

Every effect passes.

- **Fastest:** the effects at exactly 3 flashes per second (the press tell, the Pips reject, the bell lamp, the peg and the
  load lamps). They are all small emissive lamps.
- **Large-area effects:** with calm on, none flashes more than once a second.

The port's calm mode goes further than the prototype's in seven places. In each, the prototype ignores `game.calm`; the port
must not (§4.29: "Calm mode must be honoured by every flicker/shake/spark source").

- **Now in Core:**
  - the cradle's seated lamps: `Cradle.SeatedLamp(t, calm)`, which `MechanismReadout`'s lamp channel 0 reads with the
    view's calm flag. `MechanismViewBindings.For("Cradle", "SeatedLamps")` binds it as an emission gain of 6
    (`glow('SeatedLamp', 6 · flick)`, L4820), the same plumbing as the DL-01 relay lamps. Two steps remain, both outside
    Core: the `SeatedLamps` node takes its marker name (`MECH_Cradle_dl04_cradle__SeatedLamps`, now in
    `tools/unity_export/conventions.py`) on the next region export, and the `SeatedLamp` material is authored dark
    (`EMIT` intensity 0, as are the relay lamps), so the gain scales black until U-15's lighting gives the game-driven
    `EMIT` lamps a unit rest emission. That second step is U-15 work.
  - the dying eye: `DeathAct.EyeLevel`, the only eye accessor, reads calm from the mechanism graph (`MechanismGraph.Calm`,
    which `CheckpointService` sets from `Settings.Calm`) at every step and returns `DeathProfile.EyeLevel(t, calm)`. No
    Runtime renderer reads the eye yet (U-15 lights D-17's eye); it must read `DeathAct.EyeLevel` for a sinking death and
    `DeathProfile.EyeLevel(t, SettingsStore.Calm)` for a motor death.
- **Specified in `FlashEffects` for U-15:**
  - the DL-08 arc light, held steady;
  - the DL-10 UP lamps buzz, steady;
  - the DL-14 jam light, steady;
  - the DL-14 clutch sparks, none.

### Calm mode off

The prototype's look is kept. These effects fail under the conservative count:

- the opening work bulb;
- the DL-01 live cable;
- the DL-01 cord lamp;
- the DL-04 row lamps, rack lights and cradle seated lamps (the lamps only on the combined area);
- the DL-05 Ration strip;
- the DL-08 arc light;
- the DL-10 UP lamps (on the combined area) and lobby bulb;
- the DL-11 lane bulb;
- the DL-14 jam light;
- the dying eye (on the combined area, in its worst scene).

**Why none is fixed.** Every one of them is a deliberate stutter: a failing strip, a live cable, rows coming on. Bringing them
under 3 Hz would change how they look, and calm mode already steadies all of them. No behaviour pinned by the trace or parity
tests changed.

**Core changes, all behaviour-preserving:**

- The light curves were extracted as public statics: `PrologueLighting.CableLevel`, `CrankLevel`, `ScannerIdle` and
  `CandlesLevel`, and `PeriodicCrusher.LampAt`.
- The old one-argument `Cradle.SeatedLamp(t)` still returns the prototype's values. `DeathProfile.EyeLevel(t)` and
  `DeathAct.EyeLevelFor(calm)` are gone: the eye is always read with calm.

## Recommendations

1. **Show a photosensitivity warning at boot.** Calm off fails for thirteen effects, and several are large and recur: the Ration
   strip every 9 s, the lane bulb's shimmer, the DL-08 arcs every 2.4 s. Show a short warning before the title on the first run
   and after a reset, with a direct toggle for "Reduce flicker and flashes". Warnings like this are standard practice in games with flickering light.
2. **Keep calm mode off by default, but offer it on that warning screen.** Defaulting it on would hide the prototype's
   intended look from most players. Offering it on the first screen reaches the people who need it before the opening's work
   bulb, which is the first effect that fails and plays in the first 10 s. Mirror `prefers-reduced-motion` or the platform's
   reduce-flashing setting into the default where the platform exposes one. The prototype already drops its CSS fades under
   `prefers-reduced-motion` (L119).
3. **Measure it in engine once U-15 lights the scenes.** The figures here are an upper bound from the curves. Capture the real
   frames with calm off (the Ration Hall, the DL-08 tunnel, the DL-11 lane, the DL-04 reveal) and run them through a
   frame-based analyser such as PEAT or Harding. If an effect passes on real luminance, mark it here and in
   `FlashSafetyTests.CalmOffFailures`.
4. **Implement the calm curves exactly as `FlashEffects` gives them** when U-15 ports the not-yet-ported effects: the opening,
   the cord lamp, regions 4 and 5, and chapter 1. `FlashSafetyTests` then keeps them in check. A new flashing effect gets a
   `FlashEffect` entry so the test covers it.
