# Look comparison: Unity against the prototype

Two capture tools play the prologue with the same mechanical bot and save screenshots under the same names, so the
port can be checked against `game/undelivered/index.html` frame by frame. Core's bot (`PrologueScript`) has input parity
with `tools/sim/bot.js`, so D-17 stands in the same place on both sides (each `capture.json` lists his `x` per shot).

| Shot | When |
|---|---|
| `mNN_<mark>` | at each new bot mark: `opening`, `cp start`, `play`, `DL-01`, `cp shutter`, `DL-02`, … |
| `t<seconds>` | at that many seconds after the `play` mark (control comes to him) |

## Unity

`Dead Letter → Capture → Prologue Playthrough` in the editor, or headless with the GPU (no `-nographics`, no `-quit`;
the editor quits when the run ends):

```
Unity.exe -batchmode -projectPath unity/DeadLetter -logFile capture.log ^
  -executeMethod DeadLetter.Editor.Capture.PlayCapture.Run ^
  -captureOut C:\shots\unity [-captureSeed 1] [-captureTimes 0.1,1,3,10] [-captureMax 240] [-captureSize 1280x720]
```

It opens `DL_Persistent`, starts a new game from the opening (it ignores the slot and turns off pause-on-focus-loss, in
memory only), and adds `Runtime/Dev/PlaythroughCapture`, which feeds the bot through `D17Controller.InputSource`. It steps
one Core step per frame (`Time.captureFramerate` 60), so the shots don't depend on the machine's speed. The scenes must
be built first (`unity/README.md`, "Playing the prologue in Unity"). A new game writes the save slot as usual.

## The prototype

Serve the game, then run `capture_prototype.mjs` from a folder with `playwright-core` and `three@0.169.0` installed:

```
python -m http.server 8765 -d game/undelivered
npm install playwright-core three@0.169.0           # in a scratch folder; copy capture_prototype.mjs there
BOT=<repo>/tools/sim/bot.js node capture_prototype.mjs C:\shots\proto 1 0.1,1,3,10 240
```

It uses the system Chrome (`CHROME=` for another), a 1280×720 viewport (`SIZE=`), holds the bot through the title
card and skips the card with a key, then stops the game at each shot until the screenshot is taken.

## Side by side

```
python side_by_side.py C:\shots\proto C:\shots\unity C:\shots\cmp 0.5
```

One image per shot: the prototype on top, Unity below, each labelled with his `x` and the time after `play`.
