# Voice letters: the script

**Status:** draft for the director to record, 21 October 2026. Placement is in `docs/audio_audit.md`.

## The motto

The order-era tannoys all end the same way: **"Order above all."** Say it flatly, as a sign-off nobody hears any
more. The player hears it often enough that it stops meaning anything; later chapters paint it over, deface it and
finally scratch it out (`docs/story_bible.md`).

## The idea

The refuge's post carried more than paper. For the price of a stamp you could speak into a recorder at the post
counter. It cut your voice into a thin tin card, a **voice card**, and the post delivered it like a letter. Every home
had a card player: a small wooden box with a brass horn and a crank. Some cards were never delivered.
- **D-17 finds them:** in the depot, in the heap, in pockets and laps, and plays them.
- **Announcements:** the refuge also spoke through **tannoys**, wall horns that played recorded announcements on a
  schedule. With the power back, some have started again, for nobody.

**How the voices should feel:**
- Ordinary people talking, not performing. Understatement is everything.
- The dark parts are in what isn't said: "We're fine," when they were not.
- No one explains the history. Nobody says "the air was cut".
- The recordings are old, and the game makes them sound old.
- Speak naturally, and leave the processing to the game.

## How to record

- **One voice for all:** you can voice every part. The game shifts pitch, speed and tone per character (see each
  card's treatment).
  - Record children at a natural speaking pitch, a little faster and lighter; the game raises them.
  - Record elderly voices slower; the game lowers and roughens them a touch.
- **Format:**
  - mono WAV or MP3, 44.1 or 48 kHz;
  - a quiet room, the mic 15 to 20 cm away;
  - no effects.
- **Silence:** leave 1 second of silence before and after each take.
- **Files:** one file per card, named exactly as the card's id (for example `card_heap.wav`).
  - Put them in `game/undelivered/assets/voice/`. The game finds them by name, with `.mp3` first, then `.wav`.
  - Alternates: record extra takes as `card_heap_b.wav` and so on, and I'll pick one.
- **Pauses:** the subtitle times below are rough. The game spreads the lines over your recording's real length, so
  pause naturally between lines.
- **Brackets:** *[pause]*, *[breath]* and similar are directions; don't say them.

**Treatments (what the game does to your recording):**

| Name | Pitch | Speed | Band | Character |
|---|---|---|---|---|
| `tannoy` | 0 | 1.0 | 400–3000 Hz | saturated; a big hard room; a slow loop |
| `card` | 0 | 1.0 | 250–3500 Hz | crackle; light wow and flutter |
| `card_worn` | 0 | 0.97 | 300–3000 Hz | heavy crackle; deeper wow; drops |
| `child` | +5 semitones | 1.06 | as `card` | |
| `elder` | −1.5 semitones | 0.95 | as `card` | a small tremble |
| `machine` | 0 | 1.0 | 600–2600 Hz | clipped, ring-modulated a touch |
| `radio` | 0 | 1.0 | 500–2800 Hz | through static that rises and swallows it |

## The depot

### `tan_depot_1`: the start-of-shift announcement (DL-01, by the dispatch board)

Treatment `tannoy`. About 14 s.
> Night shift, to your stations. *[pause]* Night shift, to your stations.
> Sorting will run until oh-six-hundred. Couriers, report to dispatch.
> *[pause]* Thank you for your work. The refuge depends on it. *[pause]* Order above all.

### `card_sorter`: a sorter to her daughter (DL-02, the tea corner)

Treatment `card`. About 30 s.
> Hello, little bird. It's Mum. *[breath]*
> I'm on nights again, so you'll be asleep when this comes. Gran will play it for you at breakfast.
> It's warm in here tonight. Stuffy. They've turned the fans down to save power, so we're all yawning over the letters.
> *[small laugh]* Ruth fell asleep on the franking machine.
> Be good for Gran. I'll be home when the shift's done. *[pause]*
> Love you. Bye-bye. Bye.

The weight is in "stuffy" and "yawning": the air was failing, and she thought it was only tiredness.

### `tan_racks`: the courier roll-call (DL-04, faint and broken)

Treatment `tannoy`, with dropouts. About 12 s.
> Couriers to dispatch. *[pause]* D-12. *[pause]* D-13. *[pause]* D-14. *[pause]* D-15. *[pause]* D-16.
> *[long pause; the recording ends before D-17]*

## The Ration Hall

### `tan_rations`: the ration announcement (DL-05, over the hatch)

Treatment `tannoy`. About 14 s.
> Attention, grade four. Rations are suspended until further notice.
> Distribution will resume at oh-eight-hundred. *[pause]*
> Please remain in the hall. Please keep the aisles clear for the weigh-in. *[pause]* Order above all.

### `card_queue`: a card in the queue (DL-05)

Treatment `card_worn`. About 25 s.
> If someone finds this. *[pause]*
> We waited for them to open the hatch. They said eight o'clock.
> That was the eleventh. I've lost count since. *[pause]*
> There are a lot of us here. We're keeping our places.
> If you're from upstairs, *[pause]* there are children here. Please.

## Return to Sender and the Heap

### `tan_scanner`: the scanner's refusal (DL-06)

Treatment `machine`. About 3 s, played when it rejects him.
> Return to sender. *[pause]* Return to sender.

### `card_reader`: the one who stayed (DL-06, the secret room)

Treatment `elder`, light. About 40 s.
> Number two thousand and eleven. *[paper]* "Dear Tomas. The rain on ring A is only the pipes, they say, but it sounds
> like rain, and I stand under it some evenings. I hope you are eating. Your sister sends her love..."
> *[pause]*
> I read them all, in the end. Somebody ought to. *[pause]*
> Tomas, if you're out there, she sent her love. *[pause]*
> Number two thousand and twelve.

### `card_heap`: a family's card to a son (DL-07, half-buried in the heap)

Treatment `card`. About 25 s.
> Hello, love, it's your dad. *[pause]* We're fine. Your mother's fine.
> The ration's short this month, but we're fine. Don't send any of yours, I mean it.
> The lift's still not running to your level, but they say soon.
> Write when you can. We play your last one every night. *[pause]* We're fine.

## The Handbrake and the Slipping Cage

### `card_den`: the children's club (DL-09, the den)

Treatment `child`. Two or three voices, all yours, recorded separately as `card_den_1`, `card_den_2` and `card_den_3`;
the game mixes them. About 30 s.
> **1:** Is it on? Is it going?
> **2:** It's going! Say it!
> **1:** Okay. *[official]* This is the Den. If you found this, you are in the club.
> **3:** You have to say the password.
> **1:** The password is *crooked tree*.
> **2:** That's Mara's. She drew it.
> **3:** *[from further away]* Mara, say something!
> **1:** She won't, she's shy. *[giggling]* Okay. Club rules: no grown-ups. No telling. *[pause]* And whoever finds this
> has to come back.

The only time Mara is named in the prologue's voices: as a child who wouldn't speak.

### `tan_bridge`: the barrier at the cut bridge (DL-09)

Treatment `tannoy`, running slow; the game also drags its speed down. About 10 s.
> Grades one and two only beyond this point. *[pause]* Grades one and two only.
> All other residents, return to your rings. *[pause]* Thank you for your patience. *[pause]* Order above all.

## Up Only

### `tan_relocation`: the relocation announcement (DL-10, the lobby)

Treatment `tannoy`, cleaner than the others. About 16 s.
> Relocation. This car is for grades one and two. Please have your papers ready.
> One case per person. *[pause]* Do not push.
> This is the last scheduled car. *[pause]* This is the last scheduled car. *[pause]* Order above all.

### `card_lastcar`: a parent's card to a child who went up (DL-10, the queue)

Treatment `card`. About 30 s.
> Sweetheart. *[breath]* You did so well getting on.
> I'm sorry I let go of your hand so fast. They were shouting, and I wanted you on before the gate.
> You go with Aunt Ila now. Do what she tells you.
> We'll be on the next one. *[pause]* We'll be on the next one, and I'll find you. *[pause]*
> Keep your coat on. It's cold up there, they say.

## The Child at the Address

### `radio_above`: a voice on the radio (DL-11, the radio curio)

Treatment `radio`. The game buries it in static that swells and swallows it. About 12 s. This is the first living
voice in the game, and it's Mara, old, not named.
> *[static]* ...feed to C, test four. *[pause]* Load's holding. *[pause]* Well. *[a small, dry laugh]* Not that there's
> anyone down there to... *[static rises]* ...logging it anyway.

### `card_mara_parent`: the birthday card (DL-11, C-114's hall table)

Treatment `card`, the gentlest; the clearest card in the prologue. About 40 s.
> Happy birthday, my Mara. *[breath]* Nine! *[pause]*
> I'm sorry I can't be there. They need the couriers' parents on the works this month, and the lift's slow.
> So I've sent you something with the post. Don't open it till the day. *[a smile in the voice]* I mean it.
> It's for outside. *[pause]* One day there'll be an outside, and you'll need them.
> Keep drawing your trees. Don't let them tell you they have to be straight.
> *[pause]* I love you. I'll see you soon. *[pause]* Happy birthday.

This lands what the parcel is (something "for outside"; in the overview, children's outdoor boots) without opening it,
and why the tree matters. The player has carried the parcel all along. Placement: on the hall table under C-114's new
stair. Optional, but it should be easy to find.

## Chapter 1 Attendance

### `att_gate_1` to `att_gate_3`: the register (DL-12, the attendance gate)

Treatment `tannoy`, small and warm; a gentle teacher's voice. About 3 s each.
> **1** (on the strip, no coat): Good morning. Please hang your coat on your peg.
> **2** (still no coat, a second time): Coat seven, please.
> **3** (both lamps lit): Thank you. You are present.

### `att_caretaker`: the caretaker (DL-12, the lost property room)

Treatment `elder`. About 30 s.
> Lost property, week forty. *[pause]* One mitten, red. One shoe, small, left foot. A lunch tin, M.D. on the lid.
> *[pause]*
> I keep it all. Somebody'll come back for it. *[pause]*
> Register's down to one this week. Just the little one with the drawings. Sits at the front, never says a word.
> *[pause]* Good kid.

### `att_lesson`: the repeated lesson (DL-13, the apparatus's speaker)

Treatment `card`, a cheerful teacher's voice recorded long ago. About 20 s; it loops with the machine. Record it once;
the game sticks it on "grows" when the brake is thrown.
> Good morning, class. Today we will learn how a tree grows. *[pause]*
> First, the root. *[pause]* Then, the trunk. *[pause]* Then the branches reach for the light.
> And then, the leaves. *[pause]* A tree always grows straight, and tall, toward the sun. *[pause]*
> Let us watch it again.

"A tree always grows straight" is the line Mara's parent answers on the birthday card. Placed late, it pays off for
anyone who heard both.

### `att_teacher`: the last teacher (DL-14, the stock cupboard)

Treatment `card`. About 35 s.
> To the family of Mara D., class four. *[pause]*
> She's doing well. She doesn't speak much in class, but she listens to everything.
> She asked me today why the windows don't open. I told her the truth. *[pause]* I hope that was right.
> The protocol says she isn't to be left alone, so I eat my lunch with her. I don't mind.
> She's drawn on the wall behind the window panel. A tree. I haven't had it cleaned. *[pause]*
> I'll keep recording these until someone writes back. *[pause]* Take care of yourselves.

## Recording checklist

| File | Treatment | About |
|---|---|---|
| `tan_depot_1` | tannoy | 14 s |
| `card_sorter` | card | 30 s |
| `tan_racks` | tannoy | 12 s |
| `tan_rations` | tannoy | 14 s |
| `card_queue` | card_worn | 25 s |
| `tan_scanner` | machine | 3 s |
| `card_reader` | elder | 40 s |
| `card_heap` | card | 25 s |
| `card_den_1`, `card_den_2`, `card_den_3` | child | 30 s together |
| `tan_bridge` | tannoy | 10 s |
| `tan_relocation` | tannoy | 16 s |
| `card_lastcar` | card | 30 s |
| `radio_above` | radio | 12 s |
| `card_mara_parent` | card | 40 s |
| `att_gate_1`, `att_gate_2`, `att_gate_3` | tannoy | 3 s each |
| `att_caretaker` | elder | 30 s |
| `att_lesson` | card | 20 s |
| `att_teacher` | card | 35 s |

**Total:** about 7 minutes of recording.
