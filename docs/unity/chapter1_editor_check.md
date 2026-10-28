# Chapter 1 in the editor: what to check by eye

Issue #50 (U-22b) puts chapter 1 Attendance (DL-12 to DL-17) in Unity. Core is checked against the prototype step by step
(`AttendanceChapterTraceTests`, `AttendanceCameraTraceTests`, `AttendanceViewTraceTests`, `AttendancePresentationTests`).
What no test can see is how it looks. These are the director's checks.

## Build and play

1. Import the art (Dead Letter → Art → Build Region Prefabs) and the audio (Dead Letter → Audio → Import Audio), as for the
   prologue.
2. **Dead Letter → Build → Scenes → Attendance.** It writes `Assets/Scenes/DL_Persistent.unity` for chapter 1 (this replaces
   the prologue's bootstrap; build Prologue again to go back), one scene per DL-12 … DL-17, and sets the host's `startAt`
   to `school`. The log lists anything not imported.
3. **Press Play.** He starts at `school`, the arrival door of DL-12. To start elsewhere, set `GameHost → Start At` to any
   chapter 1 checkpoint: `school`, `register`, `lesson`, `gallery13`, `window`, `hatch14`, `dorm`, `corridor`, `sickbay`,
   `class6`, `dismissed`, `crossing`, `store`, `kitchen`, `workshop` (each is tested to begin, step and frame). With it
   empty the host enters as it does for any chapter (`GameHost.Start`).

## Walk DL-12 (Coats Without Children)

| Look for | Expect (prototype line) |
|---|---|
| The first frame | The bin, the bench and peg, the stand-in figure, the strip and the gate in one frame, fog light (`frameAtt`, L6472). Walking right, the camera eases into the corridor frame from x 209.6. |
| The coat | Lifting it from the bin and hanging it on peg 7: it rides in his hand and sits on the peg. |
| The strip | Stepping on: the plate's click, the PRESENT lamp lights. Without the coat on the peg, the COAT lamp shows lit (steady: the prototype's blink is not read yet, see below) and the register's buzz and voice. |
| The gate | With him (or the figure) on the strip and the coat hung, the gate rises; it slams down if he steps off. |
| The figure | Pushing the stand-in onto the strip opens the gate for him. |

Then the rest of the chapter, in any order you like: DL-13's steps clack out and fold home, the dial turns and the tree grows;
DL-14's blinds roll by their scale, the ledges fold out, the crank spins while he winds; DL-14a's door swings into the corridor
once the room is dark; DL-14b's trolley turns at each end with its beam; DL-15's lift and its gate; DL-16's bridge and latch;
DL-16a's car; DL-17's drawer, the sluices, the water in the beds and the float, the stair door.

## Known gaps (not bugs in this build)

- **Pivots and axes.** Each `MechanismView` turns about its renderers' centre unless `Has Pivot` is set. DL-14b's cone must
  turn about the trolley's centre (set its pivot to the trolley's), and hinged parts (doors, ledges, steps, the pawls) about
  their hinge: tune them on the component. Signs follow the prototype's axes and are unchecked against the art.
- **Lamps** show their calm-mode level (no blink). Unbound for now, each with its reason in `ArtExportTests.Chapter1Unbound`:
  the peg lamp, the DL-14a eye lamps, the pupil lift's lamps, the car's load lamps, DL-14's peeling panel, DL-17's valve spin,
  the DL-16a tins.
- **Shots and shake.** The side view matches the prototype; DL-15's seat shot, DL-17's drawer close-up, the secret rooms'
  shots and the `shake()` calls are not ported yet.
- **On `dismissed`** the camera starts on the balcony and pans to him over a second or two: the prototype does the same
  (`resetAtt` leaves `k15` at 1).
- **The seam** from the prologue's end into `school` in one session is a separate task (#50's out of scope).
