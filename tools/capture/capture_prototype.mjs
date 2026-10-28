// Screenshots of the prototype at the same moments as Unity's PlaythroughCapture (Dead Letter → Capture), for a
// side-by-side check of the port's look. The mechanical bot (tools/sim/bot.js) plays; Core's port of it has input parity,
// so the shot names line up: m<NN>_<mark> at each new bot mark, t<seconds> at times after the "play" mark.
//
//   node capture_prototype.mjs <outDir> [seed=1] [times=0.1,1,3,...] [maxSeconds=600]
//
// Needs playwright-core and three@0.169.0 in node_modules (run a copy of this file from a folder that has them, with
// BOT=path/to/tools/sim/bot.js), a Chrome or Chromium (CHROME=path; default: the system Chrome), and the game served at GAME (default http://127.0.0.1:8765),
// e.g. `python -m http.server 8765 -d game/undelivered`. SIZE=1280x720 sets the viewport.
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [outDir = 'captures/prototype', seedArg = '1', timesArg = '0.1,1,3,6,10,15,20,30,45,60,90,120,150,180,240', maxArg = '600'] = process.argv.slice(2);
const seed = +seedArg, maxSeconds = +maxArg;
const times = timesArg.split(',').filter(Boolean).map(Number).sort((a, b) => a - b);
const [W, H] = (process.env.SIZE || '1280x720').split('x').map(Number);
const BOT = fs.readFileSync(process.env.BOT || path.join(here, '../sim/bot.js'), 'utf8');
const threeDir = path.resolve('node_modules/three');
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--ignore-gpu-blocklist', '--enable-gpu', '--no-proxy-server', '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage({ viewport: { width: W, height: H } });
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
await page.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', (r) =>
  r.fulfill({ path: path.join(threeDir, r.request().url().split('three@0.169.0/')[1]), contentType: 'text/javascript' }));
await page.route('https://fonts.**', (r) => r.abort());
await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html');
await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
await page.addScriptTag({ content: BOT });
await page.evaluate(([s]) => window.__startBot(s, { mechanical: true, steps: 1 }), [seed]);

// Wrap the bot: when a shot is due, stop stepping (sim.steps = 0) and render every frame until Node has taken it.
await page.evaluate(([times, steps]) => {
  const sim = window.__sim, G = window.__dl01.game, bot = sim.bot.bind(sim);
  const cap = window.__cap = { pending: null, info: null, seen: 0, next: 0 };
  const pad = (n, w) => String(n).padStart(w, '0');
  sim.steps = steps;
  sim.bot = (dt) => {
    if (G.mode === 'card') return;          // the title card runs on real time: start the bot (and its clock) at the wake
    bot(dt);
    if (cap.pending) return;
    const keys = Object.keys(sim.out.marks), due = [];
    while (cap.seen < keys.length) { cap.seen++; due.push('m' + pad(cap.seen, 2) + '_' + keys[cap.seen - 1].replace(/[^A-Za-z0-9-]/g, '_')); }
    const play = sim.out.marks.play, rel = play === undefined ? null : G.clock - play;
    while (rel !== null && cap.next < times.length && rel >= times[cap.next] - 1e-9) due.push('t' + times[cap.next++].toFixed(1).padStart(6, '0'));
    if (due.length) {
      cap.pending = due;
      cap.info = { clock: +G.clock.toFixed(3), rel: rel === null ? null : +rel.toFixed(3), x: +G.x.toFixed(3), y: +G.y.toFixed(3),
        scene: window.__dl01.scene(), checkpoint: G.checkpoint, act: G.act ? G.act.kind : null };
      sim.steps = 0; sim.render = true;
    }
  };
  cap.resume = () => { cap.pending = null; sim.steps = steps; sim.render = false; };
}, [times, 8]);

await page.click('#begin');
await new Promise((r) => setTimeout(r, 1500));
await page.keyboard.press('Enter');         // any key moves the card on after 1.2 s
const shots = [];
const t0 = Date.now();
for (;;) {
  const s = await page.evaluate(() => ({ pending: window.__cap.pending, info: window.__cap.info, done: window.__sim.out.done,
    clock: window.__dl01.game.clock, play: window.__sim.out.marks.play }));
  if (s.pending) {
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
    for (const name of s.pending) {
      await page.screenshot({ path: path.join(outDir, name + '.png') });
      shots.push({ name, ...s.info });
    }
    await page.evaluate(() => window.__cap.resume());
    continue;
  }
  if (s.done || errs.length || (s.play !== undefined && s.clock - s.play > maxSeconds) || Date.now() - t0 > 40 * 60000) break;
  await new Promise((r) => setTimeout(r, 50));
}
const out = await page.evaluate(() => window.__sim.out);
delete out.trace;
fs.writeFileSync(path.join(outDir, 'capture.json'), JSON.stringify({ seed, width: W, height: H, shots, result: out, pageErrors: errs.slice(0, 5) }, null, 1));
console.log(shots.length + ' shots;', out.error || (out.done ? 'done' : 'stopped'), errs.length ? 'page errors: ' + errs[0] : '');
await browser.close();
