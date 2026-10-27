# Core/Motor

D-17's motor (`D17Motor`): a fixed-step port of the prototype's `updatePlayer` (index.html L1931–L2067), its mantle,
holds and acts. It owns his pose, the clip to play and the acts; it knows nothing about scenes, regions or checkpoints.
`MotorConfig` holds every constant with the line it comes from; `ClipTimings` the clip lengths and act frames;
`IMotorWorld` is the lane it probes (a scene's lane geometry, `BoxWorld` in tests). See `unity/README.md` for the
file list and `docs/unity/port_architecture.md` §3.1, §4.7–§4.12 for the design.

## Integrating with a scene simulator

The motor is step #4 of the prototype's frame (`step`, L8491–L8528). A scene simulator (Core `Scenes/SceneSim`) owns
the clock, the lane, the mechanism graph, the checkpoints and the scene's rules, and calls the motor and its helpers
in this order, once per 1/60 s step:

1. **#1 clock and respawn.** `clock += 1/60`. If a respawn is pending and due (`clock >= respawnAt`), reload the
   checkpoint (`CheckpointService.Reload`) and put him there with `motor.Place(x, y, facing)`; clear `respawnAt`.
2. **#3 input gate.** While a respawn is pending, feed `MotorInput.None`. While a directed moment holds him, feed
   `MomentDirector.GateInput(...)` (a skip button calls `MomentDirector.Skip(clock)`). On the step control comes back
   (`MomentDirector.ControlReturned`), run the scene's control-return beat with motor calls; DL-01's wake label is
   `motor.PlayQuirk(ClipNames.CheckLabel, cancel: false, holdFor: 3.2, cancelAfter: 2.5)` once per game
   (`labelWake`, L8104–L8110).
3. **#4 motor.** `motor.Step(input, 1/60)`. Then read this step's events (`MotorEvents`):
   - `motor.RespawnDue(out double d)`: the stuck act (at 2.0 s, d = 1.3, the fade) or the death act (at its cut,
     d = 0.6) wants the reload; set `respawnAt = clock + d` unless one is pending.
   - `motor.Shake()`: pass it to `CameraRig.Shake(amount, calm)` when > 0.
   - `motor.ActTarget` is the station or item the current act is on; an act that ended this step shows as an
     `ActEnd` event. Chained follow-ups (the latch's Flinch, DL-18's hop) are part of the same act (`ActPart` > 0):
     no scene act is needed for them.
   - Position triggers (checkpoints by x, the hall cue, a transit's start) run here, on a step with no act, mantle or
     hold before or after.
4. **#5–#7 mechanisms.** `graph.Step(1/60, PlayerPose.Of(motor))` (a scene act that owns his pose passes its own
   pose). Then the scene's rules on the graph's log. A mechanism that strands him (DL-01's trench: `TippingBridge`
   `Stranded`) → `motor.BeginStuck()`; one that kills him → `motor.Die(kind)` (holds dropped, the clip, the shake).
   Those acts ask for the respawn themselves (step 3, next step: events from calls between steps are reported with
   the next step's).
5. **After the mechanisms: escort start and #9 ride sync.** `motorSync.AfterMechanisms(motor)` (`Mechanisms/MotorSync`,
   built once from the built graph): an `IEscort` that wants him starts the escorted act (L6399), then he is placed on
   the carrier he rides (`motor.SyncRide`, L2959–L2964) and on every carrying `ILiftRide`'s floor
   (`motor.SnapToFloor`).
6. **Checkpoints, cues, moments, exit** (scene rules), reading the synced pose.
7. **#10 camera.** `D17Framing.Input(motor, aspect, noLead)` (`Camera/D17Framing`: position, facing, the act/mantle
   push, no look-ahead while holding); set `Signals`, the scene's pushes (transit, realise) and `Shot`:
   `D17Framing.LabelShot(motor, labelCentre)` while he checks his label, else the scene's own shot. Then
   `CameraRig.Step(input, 1/60)`.

The simulator clears edge-triggered input (Jump, Use) after the step (#12). Everything above is allocation-free per
step and deterministic.

Notes for parity with the prototype (golden-trace replay):

- A station with no depth (`StandZ` 0) starts its clip on the step he arrives (no turn) or finishes turning (L1846–L1850,
  L1879); stations that step in start it on the step he reaches their depth.
- Clip-frame thresholds are the prototype's `f >= n` exactly (`ClipClock`), so the 56-frame mantle ends on its 141st step.
- Falls integrate like the prototype at 60 Hz (`MotorConfig.JumpMode.Parity60Hz`): a fall from rest (walking off, a
  bonk, a ride that is gone) starts at `vy = −g/(2·60)`, as the jump's launch speed is lowered by `g/(2·60)`, so his
  height matches `vy −= g·dt; y += vy·dt` on every step. `D17Motor.Vy` is then the prototype's vy less
  `MotorConfig.ParityVelocityOffset`; the motor adds it back for the prototype's velocity thresholds.
- The latch's Flinch is chained to its Pull (one act, crouched throughout); a time threshold in seconds compares the
  clip's seconds (`ActFrame.Time >= 1.6`), not frames, as the prototype's `actions.Flinch.time >= 1.6` does.
- Known residual: DL-05's toy (L3606) turns, then spends a step in `in` with no depth before its clip; the port starts
  the clip on the turn's step, as the crank (L1879).
