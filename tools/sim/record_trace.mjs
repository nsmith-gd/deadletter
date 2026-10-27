// Golden trace recorder (U-20): runs the simulated player (bot.js) through the prototype and writes one JSON line per
// 60 Hz game step: the inputs the game consumed that step and D-17's and the scenes' state after it. The Core
// parity tests (unity/core-tests/Dl01TraceTests.cs, Dl02TraceTests.cs, Dl03TraceTests.cs) replay the inputs
// through Core and compare. Format: tools/sim/README.md.
//
//   node record_trace.mjs <seed> <out.jsonl.gz> [mechanical]
//
// Run it from a folder that has playwright-core and a local three in node_modules/ (like sim.mjs), with the game served
// at http://127.0.0.1:8765 (or GAME). CHROME = the Chromium executable; BOT = bot.js (default: next to this file);
// RNG_SEED = the seed of the page's Math.random (default 1); PROGRESS=1 prints the clock now and then.
// BOT_OPTS = JSON merged into the bot's options (e.g. '{"pressMistake":true}': a death under DL-02's press);
// UNTIL = game-clock seconds after which the recording stops (the end line then says "stopped").
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const require = createRequire(path.join(process.cwd(), 'noop.js'));            // resolve from the run folder, as sim.mjs does
const { chromium } = require('playwright-core');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const [seedArg = '1', OUT = 'trace.jsonl.gz', mode = ''] = process.argv.slice(2);
const seed = +seedArg, rngSeed = +(process.env.RNG_SEED || 1);
const BOT_OPTS = process.env.BOT_OPTS ? JSON.parse(process.env.BOT_OPTS) : null, UNTIL = +(process.env.UNTIL || 0);
const BOT = fs.readFileSync(process.env.BOT || path.join(HERE, 'bot.js'), 'utf8');
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

// In the page before any of its scripts: a seeded Math.random, and (once the bot starts) timers and the audio clock on
// game time, so everything a step does happens at the same step on every run.
const INIT = `(() => {
  // The prototype's own LCG (index.html L2666-L2667; Core SimRng.Lcg): s = (s * 16807 + 11) mod 2147483647.
  let s = ${rngSeed} % 2147483647;
  Math.random = () => { s = (s * 16807 + 11) % 2147483647; return s / 2147483647; };
  window.__seedRandom = (v) => { s = v % 2147483647; };
  // Virtual time: from __virtualTime(true) on, setTimeout callbacks run at the start of the step their delay reaches,
  // and AudioContext.currentTime reads game time (the ambience and voices schedule from it and draw Math.random).
  const realTimeout = window.setTimeout.bind(window), realClear = window.clearTimeout.bind(window);
  const queue = []; let vnow = 0, virtual = false, nextId = 1e9;
  window.setTimeout = (fn, ms = 0, ...args) => {
    if (!virtual) return realTimeout(fn, ms, ...args);
    const id = nextId++; queue.push({ id, at: vnow + Math.max(0, +ms || 0), fn, args, n: id }); return id;
  };
  window.clearTimeout = (id) => { const k = queue.findIndex((q) => q.id === id); if (k >= 0) queue.splice(k, 1); else realClear(id); };
  window.__virtualTime = (on) => { virtual = on; };
  window.__advanceTime = (ms) => {                       // fire what is due (in order of time, then of creation)
    vnow += ms;
    for (;;) {
      let k = -1;
      for (let i = 0; i < queue.length; i++) if (queue[i].at <= vnow && (k < 0 || queue[i].at < queue[k].at || (queue[i].at === queue[k].at && queue[i].n < queue[k].n))) k = i;
      if (k < 0) break;
      const q = queue.splice(k, 1)[0];
      if (typeof q.fn === 'function') q.fn(...q.args);
    }
  };
  const proto = window.BaseAudioContext && window.BaseAudioContext.prototype;
  const desc = proto && Object.getOwnPropertyDescriptor(proto, 'currentTime');
  if (desc && desc.get) Object.defineProperty(proto, 'currentTime', { configurable: true, get() { return virtual ? vnow / 1000 : desc.get.call(this); } });
})();`;

// The recorder, in the page: wraps the bot's per-step call. At step i it first stores step i-1's line (the state is
// what step i-1 left), then lets the bot set the input, then keeps a copy of the input step i will consume. Its first
// call starts the game: Math.random reseeded, timers on game time, game.clock = 0, then Begin. Nothing before it
// (the title screen's real-time frames) reaches the trace, so two runs of the same seed are identical.
const RECORDER = `window.__record = (rngSeed) => {
  const D = window.__dl01, G = D.game, I = D.input, sim = window.__sim, bot = sim.bot, SH = D.k.SH, PR = D.k2.PRESS2;
  const r6 = (v) => (typeof v === 'number' ? Math.round(v * 1e6) / 1e6 : v);
  const b = (v) => (v ? 1 : 0);
  let i = 0, inp = null, prev = {};
  window.__trace = [];
  const act = () => { const a = G.act; if (!a) return null; return a.kind + ':' + (a.kind === 'quirk' ? a.clip : a.phase); };
  const hold = () => (G.hold ? G.hold + (G.pushKey ? ':' + G.pushKey : '') : null);
  // DL-02 (U-20): the press's face (from its model: rest + (face - PRESS2.rest)), the box, the tube's letter, deaths and a
  // pending respawn. Only while in DL-02 (region 2, x < SH.x1 + 1, so its exit step too); absent fields are not written,
  // so the lines of every other step are unchanged.
  function dl02() {
    if (G.region !== 2 || !(G.x < SH.x1 + 1)) return {};
    const k = D.refs.ch1, pr = k && k.press, bx = G.ch1 && G.ch1.box;
    return {
      pf: pr ? r6(pr.position.y - pr.userData.rest.p.y + PR.rest) : null,
      bx: bx ? r6(bx.x) : null, bb: bx ? r6(bx.base) : null, bs: bx ? bx.state : null, tl: D.letters.tube ?? null, dn: G.deaths, ra: r6(G.respawnAt || 0),
    };
  }
  function state() {
    const c = G.ch1 && G.ch1.cart;
    return {
      clk: G.clock, x: r6(G.x), y: r6(G.y), z: r6(G.z), vx: r6(G.vx), vy: r6(G.vy), yaw: r6(G.yaw), f: G.facing, g: b(G.grounded), c: b(G.crouched),
      m: G.mode, a: act(), h: hold(), mt: b(G.mantle), tr: G.transit ? G.transit.stage : -1, r: G.region, cp: G.checkpoint,
      fr: r6(G.frame), clip: D.clip(), sc: D.scene(),
      rel: b(G.released), sh: r6(G.shutterAngle), lv: r6(G.leverAngle), wy: r6(G.weightY), door: r6(G.doorOpen), wh: r6(G.wheelAngle),
      cx: c ? r6(c.x) : null, cs: c ? c.state : null, cd: c ? r6(c.drop) : null, cl: c ? b(c.lip) : null, nr: G.nextRelay,
      ...dl02(),
      // DL-03: the trolley, the sort weight, the plate's load and needle, the gate.
      tx: r6(G.trolley.x), ws: G.weight.state, wx: r6(G.weight.x), wo: r6(G.weight.off), ld: r6(G.load), nd: r6(G.needle),
      gy: r6(G.gate.y), gv: r6(G.gate.v),
    };
  }
  function flush() {
    if (!inp) return;
    const full = Object.assign({}, inp, state()), line = { i: i - 1 };
    for (const k in full) if (full[k] !== prev[k]) line[k] = full[k];
    prev = full;
    window.__trace.push(JSON.stringify(line));
  }
  sim.bot = function (dt) {
    if (i === 0) { window.__seedRandom(rngSeed); window.__virtualTime(true); G.clock = 0; document.getElementById('begin').click(); }
    window.__advanceTime(1000 / 60);
    if (!sim.out.done) flush();
    bot.call(sim, dt);
    inp = { L: b(I.left), R: b(I.right), JP: b(I.jumpPressed), JH: b(I.jumpHeld), UP: b(I.usePressed), UH: b(I.useHeld), SH: b(I.shift), AX: r6(I.axis || 0) };
    i++;
  };
};`;

const browser = await chromium.launch({ executablePath: CHROME,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server', '--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
await page.addInitScript(INIT);
await page.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', (r) => r.fulfill({ path: path.join(path.resolve('node_modules/three'), r.request().url().split('three@0.169.0/')[1]), contentType: 'text/javascript' }));
await page.route('https://fonts.**', (r) => r.abort());
await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html' + (process.env.QUERY || ''));
await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
await page.addScriptTag({ content: BOT });
await page.addScriptTag({ content: RECORDER });
// One task: no frame runs between starting the bot and wrapping it; the wrapper's first call presses Begin.
await page.evaluate(([s, m, r, o]) => { window.__startBot(s, { mechanical: m === 'mechanical', steps: 10, ...(o || {}) }); window.__record(r); }, [seed, mode, rngSeed, BOT_OPTS]);

const gz = zlib.createGzip({ level: 9 });
const file = fs.createWriteStream(OUT);
gz.pipe(file);
const header = { format: 'deadletter-trace/1', game: 'game/undelivered/index.html', bot: 'tools/sim/bot.js', seed, mode: mode || 'first_playthrough',
  rngSeed, rng: 'lcg16807', step: 1 / 60, round: 1e-6, delta: true, ...(BOT_OPTS ? { botOpts: BOT_OPTS } : {}), ...(UNTIL ? { until: UNTIL } : {}) };
gz.write(JSON.stringify(header) + '\n');
const t0 = Date.now();
let out, lines = 0;
while (Date.now() - t0 < 40 * 60000) {
  await new Promise((r) => setTimeout(r, 2000));
  const chunk = await page.evaluate(() => window.__trace.splice(0));
  for (const l of chunk) gz.write(l + '\n');
  lines += chunk.length;
  out = await page.evaluate(() => ({ ...window.__sim.out, x: window.__dl01.game.x, clock: window.__dl01.game.clock }));
  if (process.env.PROGRESS) console.log('  ..', Math.round(out.clock), 'x=' + out.x.toFixed(2), lines + ' steps');
  if (out.done) break;
  if (UNTIL && out.clock >= UNTIL) { out.stopped = true; break; }
  if (errs.length) { out.error = 'page error: ' + errs[0]; break; }
}
const rest = await page.evaluate(() => window.__trace.splice(0));
for (const l of rest) gz.write(l + '\n');
lines += rest.length;
if (!out.done && !out.error && !out.stopped) out.error = 'wall timeout';
gz.write(JSON.stringify({ end: true, steps: lines, error: out.error, ...(out.stopped ? { stopped: true } : {}), marks: out.marks, events: out.events, pageErrors: errs.slice(0, 5) }) + '\n');
gz.end();
await new Promise((r) => file.on('finish', r));
console.log(seed, out.error || 'ok', lines + ' steps', JSON.stringify(out.marks), Math.round((Date.now() - t0) / 1000) + 's wall');
await browser.close();
process.exit(out.error ? 1 : 0);
