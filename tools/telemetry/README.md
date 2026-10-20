# Play telemetry

The game (`game/undelivered/index.html`, the `Telemetry` module) records anonymous play events: scene and checkpoint
changes, deaths and their cause, interactions started, button prompts shown, 25-second idles, curiosities found, the
weigh-in's readings, lift buzzes, cage dips, the White's warning, pauses and checkpoint reloads, frame rate every 10 s
of play, the end, and leaving the page. Each event has the game clock, the scene, D-17's x and the checkpoint. A
session starts with coarse device facts (touch, mobile, viewport, pixel ratio, GPU string, language) and the options.
There is no personal data; the session id is random per page load.

Players can turn it off (Options: "Share anonymous play data"); the title card says what is recorded.

## Where the data goes
- **An endpoint:** open the game with `?telemetry=https://your-host/events` (or set `window.DL_TELEMETRY_URL` before
  the game script). Batches of up to 25 events are POSTed every 15 s and when the page is hidden or closed
  (`sendBeacon`), as JSON text.
- **Always, locally:** the last events are kept in the browser, and the pause card's **Save play log** downloads them
  as a JSON file. Testers without an endpoint can send that file.

## Collecting
`collector.py` is a tiny stdlib server that appends each batch to `data/YYYY-MM-DD.jsonl` and answers CORS:

    python tools/telemetry/collector.py --port 8787 --data ./telemetry-data

Run it behind HTTPS if the game is served over HTTPS. Any service that accepts a JSON POST works the same way
(a serverless function writing to a bucket, a form backend, an analytics ingest endpoint).

## Reading
    python tools/telemetry/summarise.py telemetry-data/*.jsonl dead-letter-playlog-*.json

prints, per scene: sessions that reached it, median time in it, deaths by cause, idles, prompts and quits; the
full-chapter time; puzzle signals; and frame rate by device.
