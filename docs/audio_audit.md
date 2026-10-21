# Prologue audio audit: cues and audio interactables

**Status:** 21 October 2026.

**Why:** the director asked for small audio cues and audio interactables across the prologue, and for recorded voice
lines to be found in the world. The voice lines are in `docs/voice_script.md`.

**What exists today:**
- the synthesized `Sound` module, about 80 one-shots and loops, all generated in code;
- eleven music cues (`Music`), each now with a fade-in.

**What's missing:**
- **Place:** sounds that live somewhere in the world and get louder as he nears them.
- **Things to play:** few things the player can touch only to hear them. The radio in C-114's street is the one example.
- **Voices:** no human voice anywhere. The refuge is full of their recordings and announcements, and the player has
  never heard one.

## Three new systems

1. **Emitters.** A list of positional loops (x, height, kind, level, reach), mixed by distance to D-17 every frame and
   faded to nothing out of reach. The kinds are all synthesized:
   - drip;
   - clock tick;
   - fluorescent buzz;
   - water lapping;
   - wind (in a shaft);
   - a fan;
   - a far machine;
   - radio static;
   - a music box.
2. **Voice letters.** A small interactable, the **voice-card player**: a wooden box with a brass horn and a hand crank.
   - Use: he turns the crank, and a recording plays through the old-recording chain (below) with subtitles.
   - The refuge's post carried recorded **voice cards** (thin tin discs) as well as letters. Some never got delivered.
   - **Tannoys** (horn speakers on walls) play announcements on their own as he passes. They play once, then sometimes
     again, fainter, on a long loop.
3. **The old-recording chain**, which the director's raw recordings go through:
   1. source;
   2. speed and pitch, set per character;
   3. wow and flutter (a slow wobble of pitch);
   4. saturation;
   5. band-pass (about 250 to 3,500 Hz; narrower for tannoys);
   6. crackle and hiss mixed under;
   7. room reverb, per place;
   8. the voice bus.

   Until a recording exists, a placeholder plays: a muffled speech-like murmur shaped to the line's length, with the
   subtitle. The game works the same either way.

## Scene by scene

Legend:
- **E**: emitter;
- **C**: one-shot cue on an event;
- **I**: audio interactable (Use);
- **T**: tannoy, plays as he passes;
- **V**: voice card, on a player.

### DL-01 The Wake
- **Has:** relay pulse, hum, sparks, crank ratchet, shutter, cart.
- **E:**
  - water dripping from the burst pipe by the trench (x ≈ 6.8);
  - the dispatch board's tick as its one lit line blinks.
- **C:** the cord lamp's chain tinkles when he walks past it, if it's within reach.
- **T** `tan_depot_1`, by the dispatch board: the depot's start-of-shift announcement, still playing on the cycle the
  power came back on. Plays as he passes the board.

### DL-02 The Sorting Hall
- **Has:** tube cough, letters, franker, mugs.
- **E:**
  - the stopped extract fan's loose blade ticking in a draught over the table;
  - a fluorescent buzz under the gantry.
- **I:** the pigeonhole wall. Brushing past it rattles a few loose letters. A letter dropping into a slot gets a
  hollow paper sound.
- **V** `card_sorter`, in the tea corner, on the shelf over the mugs: a sorter's voice card to her daughter, recorded
  on the last night shift and never posted.

### DL-03 The Weight of the Job
- **E:** the gate's counterweight chain creaking while the gate is part-open.
- **C:** the dial's needle ticking as the load changes. It has one; it's quiet, so raise it.

### DL-04 The Racks
- **Has:** tubes, the row lights' cascade, the lament.
- **E:**
  - a rack lamp's failing starter, clicking now and then on one row;
  - the bay's cradle servo idling.
- **T** `tan_racks`, low in the hall, very faint and broken up: a courier roll-call ("Couriers to dispatch. D-12, D-13,
  D-14 ...") that stops at D-16. He is D-17.

### DL-05 The Ration Hall
- **E:**
  - flies? No: nothing alive. A dripping tap behind the counter instead;
  - the shrine's candle flames guttering (a very faint, irregular whisper).
- **T** `tan_rations`, over the hatch: the ration announcement. It promises resumption at a time that has long passed,
  then loops.
- **V** `card_queue`, in the queue's lap, the second seated figure's: a voice card one of them recorded for whoever
  would come after.

### DL-06 Return to Sender
- **Has:** belt, klaxon, scanner, carriers.
- **E:** the scanner's mains hum.
- **I:** the scanner's speaker. It already rejects him; give it a voice: `tan_scanner`, "Return to sender".
- **V** `card_reader`, in the secret room (the one who stayed), on his lap: him reading aloud a dead letter, to no one.

### DL-07 The Heap
- **Has:** heap slides, the clock.
- **E:** paper shifting in the heap now and then (a slow slide and a hiss of envelopes).
- **V** `card_heap`, half-buried in the heap at the gallery's foot: an ordinary family's voice card to a son on ring A.
  "We're fine." Never delivered.

### DL-08 The Handbrake
- **Has:** lift crash, pawl, the White's water.
- **E:**
  - the sump's water lapping (where the White lives; a natural danger cue, louder near the edge);
  - the goods lift's snapped cable swinging and ticking against the shaft.
- **C:** a suitcase in the wreck creaks as its lid settles when he passes.

### DL-09 The Slipping Cage
- **Has:** cage, hopscotch, the coin viewer.
- **E:**
  - in the tunnel, the den's music box. It plays a few slow notes when he is near the vent, as the cue to the
    secret room;
  - wind on the balcony.
- **I:** the music box inside the den: Use to wind it, and it plays its tune.
- **V** `card_den`, in the den: the children's club message.
- **T** `tan_bridge` at the cut bridge: GRADES 1–2 BEYOND THIS POINT, read out by a recorded voice on a loop that has
  run down.

### DL-10 Up Only
- **Has:** the lift and its gauge.
- **T** `tan_relocation`, in the lobby: the relocation announcement ("Relocation: this car is for grades one and two
  ..."). It is the loudest and clearest recording in the prologue, because it was the newest.
- **V** `card_lastcar`, in the waiting queue: a parent's card to a child who went up without them.

### DL-11 The Child at the Address
- **Has:** radio, switch, doorbell, knock, the White.
- **E:**
  - water lapping along the flooded lane;
  - the well's wind at the ending landing;
  - the splice box's new hum (the only fresh sound in ring C). It should be heard before the look up.
- **I:** the radio. Today it tunes static. Make it find, for a moment, a voice from far above: `radio_above`. It is the
  first sign anyone is alive.
- **V** `card_mara_parent`, in C-114, on the hall table under the stair: Mara's parent, recorded for her ninth
  birthday, to go with the parcel. This is the emotional centre of the prologue's voices; see the script.

## Chapter 1 Attendance (built with DL-12 to DL-14)

| Scene | Audio |
|---|---|
| DL-12 | **T** `att_gate_1` to `att_gate_3`, the register's voice at the gate: "Good morning. Please hang your coat on your peg." "Coat seven, please." "Thank you. You are present." **V** `att_caretaker`, in the lost property room. |
| DL-13 | The lesson, `att_lesson`, from the horn speaker, looping with the machine and sticking on a word when it is braked. **E:** the apparatus's clockwork. |
| DL-14 | **E:** the blinds' chain over its pulleys. **V** `att_teacher`, in the stock cupboard. |

## What gets built now

| Item | Who |
|---|---|
| Emitters, the voice chain, voice cards and tannoys, placeholders and subtitles | Game: the lead |
| Voice-card player and tannoy props, placed where this audit says, plus the den's music box | Art: one agent, `art/pass7` |
| Attendance's players and speakers | The Attendance scene agents |
| Recordings | The director (`docs/voice_script.md`). Drop the files into `game/undelivered/assets/voice/` with the names in the script and they replace the placeholders. |
