// Golden trace recorder (U-20): runs the simulated player (bot.js) through the prototype and writes one JSON line per
// 60 Hz game step: the inputs the game consumed that step and D-17's and the scenes' state after it. The Core
// parity tests (unity/core-tests/Dl01TraceTests.cs … Dl06TraceTests.cs, PrologueChapterTraceTests.cs) replay the inputs
// through Core and compare. Format: tools/sim/README.md.
//
//   node record_trace.mjs <seed> <out.jsonl.gz> [mechanical]
//
// Run it from a folder that has playwright-core and a local three in node_modules/ (like sim.mjs), with the game served
// at http://127.0.0.1:8765 (or GAME). CHROME = the Chromium executable; BOT = bot.js (default: next to this file);
// RNG_SEED = the seed of the page's Math.random (default 1); PROGRESS=1 prints the clock now and then.
// BOT_OPTS = JSON merged into the bot's options (e.g. '{"pressMistake":true}': a death under DL-02's press);
// UNTIL = game-clock seconds: the recording stops, inside the page, after the first step whose clock is >= UNTIL (that
// step is the last line; the end line then says "stopped"), so a stopped trace ends on the same step on every run.
// The header carries the sha256 of the index.html the page loaded (as served), so a trace names the game it was taken from.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
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
  // The last 2^18 states drawn (it changes no draw): DL-08's recorder finds a crate's draws in it (dl08, rs8).
  const ring = new Int32Array(1 << 18); let rn = 0;
  Math.random = () => { s = (s * 16807 + 11) % 2147483647; ring[rn++ & 262143] = s; return s / 2147483647; };
  window.__rngRing = () => ({ ring, n: rn });
  // How many draws fn makes, with the generator put back as it was (used before the run's reseed).
  window.__countDraws = (fn) => { const s0 = s, n0 = rn; fn(); const d = rn - n0; s = s0; rn = n0; return d; };
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
const RECORDER = `window.__record = (rngSeed, until) => {
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
  // DL-04 (U-20): the fallen courier (x, state), the cradle's arms (rotation.x), the bay door (0..1) and what the bay
  // wants (want: him on the plate, or the courier seated; read back from the plate's 1 cm dip). Only while in DL-04
  // (region 2, x from GATE_X 30.6 to RATION5.x0 + 1, so its exit step too); absent fields are not written.
  function dl04() {
    if (G.region !== 2 || !(G.x >= 30.6 && G.x < D.k2.RATION5.x0 + 1)) return {};
    const k = D.refs.ch1, cr = G.ch1 && G.ch1.courier, p = k && k.bayPlate;
    return {
      kx4: cr ? r6(cr.x) : null, ks4: cr ? cr.state : null, ka4: k && k.armL ? r6(k.armL.rotation.x) : null,
      bd4: G.ch1 ? r6(G.ch1.bayDoor) : null, bw4: p && p.userData.y0 != null ? r6((p.userData.y0 - p.position.y) / 0.01) : null,
    };
  }
  // DL-05 (U-20): the drum and the body (x, state), the weigh-in (W as updateCh1 weighs it, L4890-L4892; its reading,
  // needle, plate dip; the hatch's twitch lift, L4920), the hatch's height and the SERVED flag. Only while in DL-05
  // (region 2, x >= RATION5.x0) and on the step he leaves it; names end in 5 so no other scene's fields collide.
  const R5 = D.k2.RH5, X5 = D.k2.RATION5.x0;
  let in05 = false;
  function dl05() {
    const now = G.region === 2 && G.x >= X5, emit = now || in05;
    in05 = now;
    const s = G.ch1;
    if (!emit || !s || !s.drum) return {};
    const dr = s.drum, bd = s.body, rh = s.rh, sc = s.weigh;
    const on = (x, half) => Math.min(1, Math.max(0, (Math.min(x + half, R5.plate[1]) - Math.max(x - half, R5.plate[0])) / (2 * half)));
    const meOn = G.region === 2 && G.y < 0.05 && G.x > R5.plate[0] && G.x < R5.plate[1];
    const tw = rh.served ? 0 : Math.max(0, 1 - (G.clock - (sc.twitchAt ?? -9)) / 0.9);
    return {
      d5x: r6(dr.x), d5s: dr.state, b5x: r6(bd.x), b5s: bd.state,
      w5: r6(on(bd.x, R5.bodyHalf) + 1.7 * on(dr.x, 0.225) + (meOn ? 0.2 : 0)), w5r: sc.reading, n5: r6(sc.needle), p5: r6(sc.dip),
      t5: r6(tw > 0 ? 0.14 * Math.sin(Math.PI * (1 - tw)) : 0), h5: r6(rh.h), f5: r6(rh.flag), s5: b(rh.served),
    };
  }
  // DL-06 (U-20): the scanner (phase, its clock), the belt and the route, the two levers' angles as the levers set them
  // (game.leverHold's angle in an act, else the rest angle; L2833-L2834 before the view's easing), what he rides, and the
  // carriers as one JSON string (so unchanged steps stay deltas): per carrier [id, state, route, x, y, s, wait, t, ridden,
  // tip (pivot.rotation.z), payload [[size, z, yaw], ...]] (index.html L2660-L2751). Only while sceneName() is DL-06 and on
  // the step he leaves it; names end in 6 so no other scene's fields collide.
  let in06 = false;
  function dl06() {
    const now = /^DL-06/.test(D.scene()), emit = now || in06;
    in06 = now;
    if (!emit || !D.refs.carriers) return {};
    const sc = G.scan, lh = G.leverHold, run = G.belt.running;
    const cr = D.refs.carriers.map((c) => [c.id, c.state, c.route, r6(c.root.position.x), r6(c.root.position.y), r6(c.s), r6(c.wait), r6(c.t), b(c.ridden),
      r6(c.pivot.rotation.z), c.payload.map((m) => [r6(m.geometry.parameters.height), r6(m.position.z), r6(m.rotation.y)])]);
    return {
      sp6: sc.phase, st6: r6(sc.t), bl6: b(run), rt6: G.route,
      sl6: r6(lh && lh.which === 'stop' ? lh.angle : run ? -18 : 6), pl6: r6(lh && lh.which === 'points' ? lh.angle : G.route === 'exit' ? 6 : -18),
      rd6: G.riding ? G.riding.id : null, cr6: JSON.stringify(cr),
    };
  }
  // DL-07 (U-21): the two sorting weights (state, x, base, and a tumble's progress T.t while one tumbles toward the
  // bucket, L4957-L4962), the bucket's count and the gate's height (game.ch1.bucket, gate6, L4826-L4832), the gallery
  // (game.upper), the collapse (s.collapse 0/1/2 and its clock, L7355-L7364), the heap letter (letterState.heap and
  // s.heapT, L4840-L4847), the belt, the route, the two levers and what he rides as DL-06's fields, and the carriers as
  // DL-06's cr6 with each tub's loads (the weight's index + 1, or 0) and whether its parcels are hidden. Only while
  // sceneName() is DL-07 and on the step he leaves it; names end in 7 so no other scene's fields collide.
  let in07 = false;
  function dl07() {
    const now = /^DL-07/.test(D.scene()), emit = now || in07;
    in07 = now;
    const s = G.ch1;
    if (!emit || !s || !s.weights || !D.refs.carriers) return {};
    const lh = G.leverHold, run = G.belt.running, ws = s.weights, li = (w) => (w ? ws.indexOf(w) + 1 : 0);
    const cr = D.refs.carriers.map((c) => [c.id, c.state, c.route, r6(c.root.position.x), r6(c.root.position.y), r6(c.s), r6(c.wait), r6(c.t), b(c.ridden),
      r6(c.pivot.rotation.z), c.payload.map((m) => [r6(m.geometry.parameters.height), r6(m.position.z), r6(m.rotation.y)]),
      li(c.load), li(c.load2), b(c.payload.some((m) => !m.visible))]);
    const w = (k) => ws[k] || {};
    return {
      w0s7: w(0).state ?? null, w0x7: r6(w(0).x ?? null), w0b7: r6(w(0).base ?? null), w0t7: w(0).state === 'tumble' ? r6(w(0).tumble.t) : null,
      w1s7: w(1).state ?? null, w1x7: r6(w(1).x ?? null), w1b7: r6(w(1).base ?? null), w1t7: w(1).state === 'tumble' ? r6(w(1).tumble.t) : null,
      bk7: s.bucket, g7: r6(s.gate6), up7: b(G.upper), co7: s.collapse, ct7: r6(s.collapseT), hl7: D.letters.heap ?? null, ht7: r6(s.heapT),
      bl7: b(run), rt7: G.route, sl7: r6(lh && lh.which === 'stop' ? lh.angle : run ? -18 : 6), pl7: r6(lh && lh.which === 'points' ? lh.angle : G.route === 'exit' ? 6 : -18),
      rd7: G.riding ? G.riding.id : null, cr7: JSON.stringify(cr),
    };
  }
  // DL-08 (U-21): the goods trolley (x, t.v), the pan's load (panLoad, L3026-L3029, recomputed after the step), Lift 2's
  // platform (h, v, latched, lurch; L3171-L3197), the pawl's lever as the act sets it (game.pawlHold, else the rest angle
  // LEVER_NEAR/AWAY, before the view's easing, L3211) and its dip, the returns belt (belt4.state, t, next; L3218-L3225),
  // the turn flaps' swing (L3146-L3148) and the crates as one JSON string ([type, state, x, y, z, t, spin] each, L3134),
  // and, on the step a crate spawns, the three LCG states its draws took (rs8: the type's, the spin's and the next
  // interval's, L3130, L3134, L3144), found in the ring of draws: the page's Math.random is shared by everything (the
  // clone's uuids and the scrape's noise draw between them), so a replay feeds these to the belt. Only while sceneName()
  // is DL-08 and on the step he leaves it; names end in 8 so no other scene's fields collide.
  let in08 = false;
  const seen08 = new Set(), M8 = 2147483647;
  // The draws spawnCrate's clone(true) of each template makes (its objects' uuids), counted now, before the run's reseed.
  const cloneDraws8 = (D.refs.crateTemplates || []).map((m) => window.__countDraws(() => m.clone(true)));
  function crateDraws(c, next) {
    const { ring, n } = window.__rngRing(), at = (k) => ring[k & 262143], lo = Math.max(0, n - 262144);
    let k3 = -1, k2 = -1;
    for (let k = n - 1; k >= lo && k3 < 0; k--) if (2.9 + (at(k) / M8) * 1.3 === next) k3 = k;
    for (let k = k3 - 1; k >= lo && k2 < 0; k--) if ((at(k) / M8 - 0.5) * 0.4 === c.spin) k2 = k;
    const k1 = k2 - 1 - cloneDraws8[c.type], r = at(k1) / M8, type = r < 0.55 ? 0 : r < 0.85 ? 1 : 2;
    if (k3 < 0 || k2 < 0 || k1 < lo || type !== c.type) throw new Error('dl08: crate draws not found at clock ' + G.clock);
    return [at(k1), at(k2), at(k3)];
  }
  function dl08() {
    const now = /^DL-08/.test(D.scene()), emit = now || in08;
    in08 = now;
    if (!emit || !G.plat || !G.trolley4 || !G.belt4) return {};
    const t = G.trolley4, p = G.plat, b4 = G.belt4, crates = D.refs.crates || [];
    let rs = null;
    for (const c of crates) if (!seen08.has(c)) { seen08.add(c); rs = crateDraws(c, b4.next); }
    const k = Math.min(1, Math.max(0, (t.x - (83.5 - 0.36 + 0.1)) / (2 * 0.36 - 0.2)));                    // panTrolleyK, L3023
    const on = G.region === 4 && G.x > 83.5 - 0.04 && G.x < 84.9 + 0.04 && G.y < 1.6 + 0.6;               // PAN, DECK, L3027
    return {
      tx8: r6(t.x), tv8: r6(t.v), pn8: r6(1.05 * k + (on ? 0.5 : 0)),
      ph8: r6(p.h), pv8: r6(p.v), la8: b(p.latched), lu8: b(p.lurch),
      pw8: r6(G.pawlHold ?? (p.latched ? 6 : -18)), pd8: r6(G.pawlDip || 0),
      bs8: b4.state, bt8: r6(b4.t), bn8: r6(b4.next), fl8: r6(D.refs.TurnFlaps ? D.refs.TurnFlaps.rotation.x : 0),
      cr8: JSON.stringify(crates.map((c) => [c.type, c.state, r6(c.x), r6(c.y ?? null), r6(c.z), r6(c.t), r6(c.spin)])), rs8: rs,
    };
  }
  // DL-09 (U-21): the cage (c.phase, c.y, its slip speed c.v, its clock c.t, the pawl thrown, caught once, needs a step
  // out, readyAt; L5011-L5095), the balance gauge's needle (c.needle, L5054), the two plates (state, x, base, seat;
  // L4109, L4398-L4402), the counterweight's and the cage's persist flags (persist.cw, cageDanger), the cable (shocks
  // this life, the first-touch flag, the arcs' clock game.clock % ARC_PERIOD; L7398-L7414), the tunnel's triggers
  // (dl4.hopped, dl4.awed, L3426-L3436), the refuge moment's clock and cut (L915, L953), the act's clock (game.act.t),
  // deaths and a pending respawn. Only while sceneName() is DL-09 and on the step he leaves it; names end in 9 so no
  // other scene's fields collide.
  let in09 = false;
  function dl09() {
    const now = /^DL-09/.test(D.scene()), emit = now || in09;
    in09 = now;
    const s = G.ch1;
    if (!emit || !s || !s.cage || !s.plates) return {};
    const c = s.cage, P = D.persist, d4 = G.dl4 || {}, p = (k) => s.plates[k] || {}, mt = D.Music.momentTime('refuge');
    const n = (v) => (v === undefined ? null : r6(v));
    return {
      cp9: c.phase, cy9: r6(c.y), cv9: r6(c.v), ct9: r6(c.t), th9: b(c.thrown), co9: b(c.caughtOnce), ne9: b(c.needExit), ry9: r6(c.readyAt), nd9: r6(c.needle ?? 0),
      p0s9: p(0).state ?? null, p0x9: n(p(0).x), p0b9: n(p(0).base), p0q9: p(0).seat ?? null,
      p1s9: p(1).state ?? null, p1x9: n(p(1).x), p1b9: n(p(1).base), p1q9: p(1).seat ?? null,
      cw9: P.cw ?? 0, dg9: b(P.cageDanger), so9: b(P.shockedOnce), sk9: s.shocked || 0, ta9: r6(D.arcT()),
      hp9: b(d4.hopped), aw9: b(d4.awed), mt9: mt == null ? null : r6(mt), mc9: b(G.momentCut), at9: G.act && typeof G.act.t === 'number' ? r6(G.act.t) : null,
      dn9: G.deaths, ra9: r6(G.respawnAt || 0),
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
      ...dl04(),
      ...dl05(),
      ...dl06(),
      ...dl07(),
      ...dl08(),
      ...dl09(),
    };
  }
  window.__stopped = false;
  function flush() {
    if (!inp) return;
    const full = Object.assign({}, inp, state()), line = { i: i - 1 };
    for (const k in full) if (full[k] !== prev[k]) line[k] = full[k];
    prev = full;
    window.__trace.push(JSON.stringify(line));
    if (until && G.clock >= until) window.__stopped = true;          // this step's line is the last
  }
  sim.bot = function (dt) {
    if (window.__stopped) return;                                     // stopped at UNTIL: nothing more is recorded or played
    if (i === 0) { window.__seedRandom(rngSeed); window.__virtualTime(true); G.clock = 0; document.getElementById('begin').click(); }
    window.__advanceTime(1000 / 60);
    if (!sim.out.done) flush();
    if (window.__stopped) return;
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
const resp = await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html' + (process.env.QUERY || ''));
const sha256 = crypto.createHash('sha256').update(await resp.body()).digest('hex');           // the game as the page loaded it
await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
await page.addScriptTag({ content: BOT });
await page.addScriptTag({ content: RECORDER });
// One task: no frame runs between starting the bot and wrapping it; the wrapper's first call presses Begin.
await page.evaluate(([s, m, r, o, u]) => { window.__startBot(s, { mechanical: m === 'mechanical', steps: 10, ...(o || {}) }); window.__record(r, u); }, [seed, mode, rngSeed, BOT_OPTS, UNTIL]);

const gz = zlib.createGzip({ level: 9 });
const file = fs.createWriteStream(OUT);
gz.pipe(file);
const header = { format: 'deadletter-trace/1', game: 'game/undelivered/index.html', sha256, bot: 'tools/sim/bot.js', seed, mode: mode || 'first_playthrough',
  rngSeed, rng: 'lcg16807', step: 1 / 60, round: 1e-6, delta: true, ...(BOT_OPTS ? { botOpts: BOT_OPTS } : {}), ...(UNTIL ? { until: UNTIL } : {}) };
gz.write(JSON.stringify(header) + '\n');
const t0 = Date.now();
let out, lines = 0;
while (Date.now() - t0 < 40 * 60000) {
  await new Promise((r) => setTimeout(r, 2000));
  const chunk = await page.evaluate(() => window.__trace.splice(0));
  for (const l of chunk) gz.write(l + '\n');
  lines += chunk.length;
  out = await page.evaluate(() => ({ ...window.__sim.out, x: window.__dl01.game.x, clock: window.__dl01.game.clock, stopped: window.__stopped }));
  if (process.env.PROGRESS) console.log('  ..', Math.round(out.clock), 'x=' + out.x.toFixed(2), lines + ' steps');
  if (out.done || out.stopped) break;
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
