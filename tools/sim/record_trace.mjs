// Golden trace recorder (U-20): runs the simulated player (bot.js) through the prototype and writes one JSON line per
// 60 Hz game step: the inputs the game consumed that step and D-17's and the scenes' state after it. The Core
// parity tests (unity/core-tests/Dl01TraceTests.cs … Dl06TraceTests.cs) replay the inputs
// through Core and compare. Format: tools/sim/README.md.
//
//   node record_trace.mjs <seed> <out.jsonl.gz> [mechanical]
//
// Run it from a folder that has playwright-core and a local three in node_modules/ (like sim.mjs), with the game served
// at http://127.0.0.1:8765 (or GAME). CHROME = the Chromium executable; BOT = bot.js (default: next to this file);
// RNG_SEED = the seed of the page's Math.random (default 1); PROGRESS=1 prints the clock now and then.
// BOT_OPTS = JSON merged into the bot's options (e.g. '{"pressMistake":true}': a death under DL-02's press);
// UNTIL = game-clock seconds after which the recording stops (the end line then says "stopped").
// CHAPTER=att records Chapter 1 Attendance from its first checkpoint (`school`), as sim.mjs plays it: the school's set
// is loaded before the bot starts, so the first step's startAt runs synchronously (no await) and the run stays
// deterministic. The header then has `chapter` and `start`. In region 6 the prologue's DL-06 carrier line is held off
// (see the step wrapper): it leaks into the school otherwise.
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
const CHAPTER = process.env.CHAPTER || '', START_CP = { att: 'school' }[CHAPTER] || '';
if (CHAPTER && !START_CP) throw new Error('CHAPTER: only att is recorded');
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
const RECORDER = `window.__record = (rngSeed, startCp) => {
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
  // Chapter 1 (U-22): game.att, only in region 6 (so no prologue line changes). Names end in the scene's number.
  // DL-12: the coat (x, base, state), the stand-in figure (x, v), the gate (y, fall speed), someone on the strip and
  // how many times (index.html L5228-L5243, L5381-L5408); and, for the whole chapter, what an 'att' act is about (aw:
  // game.act.what, as beginAtt names it: coat, hang, pawl, crank, duct ...).
  const A6 = () => (G.region === 6 && G.att ? G.att : null);
  function dl12() {
    const s = A6(); if (!s) return {};
    return { aw: G.act && G.act.kind === 'att' ? G.act.what : null, c12x: r6(s.coat.x), c12b: r6(s.coat.base), c12s: s.coat.state, f12x: r6(s.fig.x), f12v: r6(s.fig.v), g12y: r6(s.gateY), g12v: r6(s.gateV), p12: b(s.present), pc12: s.presentCount };
  }
  // DL-13: the second figure (x, v), the lesson (on, its clock, braked, the three steps, the tree) (L5409-L5436).
  function dl13() {
    const s = A6(); if (!s) return {};
    const L = s.lesson;
    return { f13x: r6(s.fig2.x), f13v: r6(s.fig2.v), l13: b(L.on), t13: r6(L.t), k13: b(L.braked), s13: L.steps.map(r6).join(','), tr13: r6(L.tree) };
  }
  // DL-14: the blinds (a, b and their targets), the winds, the jam, the pole (x, base, state), the peel, the chain
  // rattling against the pole, the duct taken (L5437-L5511).
  function dl14() {
    const s = A6(); if (!s) return {};
    const B = s.blinds;
    return { ba14: r6(B.a), bb14: r6(B.b), ta14: B.ta, tb14: B.tb, w14: B.winds, j14: b(s.jammed), px14: r6(s.pole.x), pb14: r6(s.pole.base), ps14: s.pole.state,
      pe14: r6(s.peel), pd14: b(s.peeled), rt14: b(s.rattle), du14: b(s.duct) };
  }
  // DL-14a: the night-light (its clock, braked), the blinds W1/W2 and their targets, the winds, the door (0..1, open),
  // the gown and the bag (x, base, state) (L5912-L5916, L6015-L6105, L6217-L6228).
  const J = (a) => a.map(r6).join(',');
  function dl14a() {
    const s = A6(); if (!s || !s.f14a) return {};
    const A = s.f14a, g = A.gown, bg = A.bag;
    return { nt14a: r6(A.t), nk14a: b(A.braked), w1a: r6(A.w1), w2a: r6(A.w2), t1a: A.t1, t2a: A.t2, wn14a: A.winds, do14a: r6(A.door), op14a: b(A.open),
      gx14a: r6(g.x), gb14a: r6(g.base), gs14a: g.state, bx14a: r6(bg.x), bb14a: r6(bg.base), bs14a: bg.state };
  }
  // DL-14b: the escort trolley (x, direction, mode, its mode clock), the figure in the bay (x, state, out, kept), the
  // hiding (L5917, L6106-L6135, L6352-L6434).
  function dl14b() {
    const s = A6(); if (!s || !s.f14b) return {};
    const B = s.f14b, f = B.fig;
    return { tx14b: r6(B.tx), td14b: B.dir, tm14b: B.mode, tt14b: r6(B.mt), fx14b: r6(f.x), fs14b: f.state, fo14b: r6(f.out), fk14b: b(f.kept), hd14b: r6(B.hide) };
  }
  // DL-15: the two figures (x, base, state, lean), the pupil lift (height, speed), the seat lamps, him seated, the
  // dismissal and the class door (L5538-L5585, L5709-L5736).
  function dl15() {
    const s = A6(); if (!s || !s.f15) return {};
    const F = s.f15, A = F.A, B = F.B;
    return { ax15: r6(A.x), ab15: r6(A.base), as15: A.state, al15: r6(A.lean), bx15: r6(B.x), bb15: r6(B.base), bs15: B.state, bl15: r6(B.lean),
      li15: r6(F.lift), lv15: r6(F.liftV), lm15: F.lamps.join(','), se15: b(F.seated), di15: b(F.dismissed), do15: r6(F.door) };
  }
  // DL-16: the bridge, the latch, the lever held, the figures stored, the rack's counterweight (L5737-L5770).
  function dl16() {
    const s = A6(); if (!s || !s.f16) return {};
    const F = s.f16;
    return { br16: r6(F.bridge), la16: b(F.latched), he16: b(F.held), sn16: F.storedN, cw16: r6(F.cw) };
  }
  // DL-16a: the stool (x, state), the dumbwaiter (height, mode, its clock), the tins and the books (x, base, state)
  // (L5918-L5921, L6136-L6192, L6233-L6246).
  function dl16a() {
    const s = A6(); if (!s || !s.f16a) return {};
    const F = s.f16a, it = (q) => [r6(q.x), r6(q.base), q.state].join(',');
    return { sx16a: r6(F.stool.x), ss16a: F.stool.state, h16a: r6(F.h), m16a: F.mode, mt16a: r6(F.mt), t1_16a: it(F.tin1), t2_16a: it(F.tin2), bk16a: it(F.books) };
  }
  // DL-17: the tray (x, base, state), the drawer, read, the T-key, the sluices, the tank and its run, the beds, the
  // float latch, the stair door, the end (L5520-L5532, L5695-L5708, L5773-L5794, L6247-L6259).
  function dl17() {
    const s = A6(); if (!s || !s.f17) return {};
    const d = s.f17, t = d.tray;
    return { ty17: [r6(t.x), r6(t.base), t.state].join(','), dr17: r6(d.drawer), rd17: b(d.read), ky17: b(d.key), sl17: d.sluice.join(','), tk17: r6(d.tank),
      ru17: r6(d.run), be17: J(d.beds), lt17: r6(d.latch), ld17: b(d.latched), do17: r6(d.door17 || 0), en17: b(s.ended) };
  }
  // Chapter 1's camera (U-22b), only in region 6 (so no prologue line changes): the side view after the framing step
  // (updateCamera's cam, L7787-L7804: frameAtt/frameAtt2, the push, the lag), before applyShots blends in an authored
  // shot. Position (cam.x, cam.y, cam.dist), look target (cam.x, cam.look, 0), the vertical fov three.js gives the 35 mm
  // base focal at the page's aspect, and the frame's fog density.
  const CAM = D.cam, CAMERA = D.camera;
  function cam6() {
    if (G.region !== 6) return {};
    return { camx6: r6(CAM.x), camy6: r6(CAM.y), camz6: r6(CAM.dist), lookx6: r6(CAM.x), looky6: r6(CAM.look), lookz6: 0,
      fov6: r6(2 * Math.atan(0.5 * CAMERA.getFilmHeight() / 35) * 180 / Math.PI), fog6: r6(D.world.fog.density) };
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
      ...dl12(),
      ...dl13(),
      ...dl14(),
      ...dl14a(),
      ...dl14b(),
      ...dl15(),
      ...dl16(),
      ...dl16a(),
      ...dl17(),
      ...cam6(),
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
    if (i === 0) { window.__seedRandom(rngSeed); window.__virtualTime(true); G.clock = 0; if (startCp) D.startAt(startCp); else document.getElementById('begin').click(); }
    window.__advanceTime(1000 / 60);
    if (!sim.out.done) flush();
    // CHAPTER: the prologue's DL-06 carrier line runs on under the school (resetWorld starts its belt at every checkpoint
    // past 'scanned', L8015+), and each chute tip startles him anywhere past x 67.8 on the floor (L2734 has no region
    // test), every 6 s, drawing Math.random. That is a leak, not chapter 1: in region 6 the belt is held off and no
    // carrier exists, so nothing of DL-06 reaches the trace. Nothing else read in region 6 depends on them.
    if (startCp && G.region === 6 && D.refs.carriers) { G.belt.running = false; D.refs.carriers.length = 0; }
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
// CHAPTER: load the school's set first (startAt loads it and starts play; the title comes back at once, in the same
// task, so no frame plays it), then the recorder's first step starts there again, synchronously.
if (START_CP) await page.evaluate(async (cp) => { const D = window.__dl01; await D.startAt(cp); D.game.mode = 'title'; }, START_CP);
// One task: no frame runs between starting the bot and wrapping it; the wrapper's first call presses Begin (or starts at
// the chapter's checkpoint).
await page.evaluate(([s, m, r, o, ch, cp]) => { window.__startBot(s, { mechanical: m === 'mechanical', steps: 10, ...(o || {}), ...(ch ? { chapter: ch } : {}) }); window.__record(r, cp); }, [seed, mode, rngSeed, BOT_OPTS, CHAPTER, START_CP]);

const gz = zlib.createGzip({ level: 9 });
const file = fs.createWriteStream(OUT);
gz.pipe(file);
const header = { format: 'deadletter-trace/1', game: 'game/undelivered/index.html', bot: 'tools/sim/bot.js', seed, mode: mode || 'first_playthrough',
  rngSeed, rng: 'lcg16807', step: 1 / 60, round: 1e-6, delta: true, ...(BOT_OPTS ? { botOpts: BOT_OPTS } : {}), ...(UNTIL ? { until: UNTIL } : {}),
  ...(CHAPTER ? { chapter: CHAPTER, start: START_CP } : {}) };
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
