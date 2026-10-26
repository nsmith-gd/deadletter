// Renders the web build's synthesized SFX to art/sfx/out/ as 48 kHz 16-bit WAV, by running the game's own Sound,
// Ambience and Voice modules (extracted from game/undelivered/index.html at run time) in an OfflineAudioContext.
//   node render.mjs            render everything, write art/sfx/out/manifest.json
//   node render.mjs thud step  render only entries whose name contains one of the words
import path from 'node:path';
import { writeFileSync, mkdirSync } from 'node:fs';
import { Session, OUT, SR, moduleSource, blockSource, patch, hash, trim, loopify, isMono, writeWav, stats, dbfs } from './lib.mjs';

// ---------------------------------------------------------------------------------------------------------------
// One-shots from Sound (index.html ~559-774). Each entry: [file name, call, opts]. The call's arguments are the ones
// the game passes at its call sites (node callsites.mjs). Amplitude-only parameters (v, strength, soft) are rendered
// at 1 and applied as a volume in Unity; parameters that change pitch or timing get one file per value used.
// opts.takes: random content (Math.random in the synth), so several takes for Unity to pick between; only the first
// take also gets a _wet file. opts.len: render window in seconds before trimming.
// ---------------------------------------------------------------------------------------------------------------
const servo = (d, f0, f1, p) => [`mech_servo_${Math.round(d * 1000)}_${f0}_${f1}`, (S) => S.servo(d, f0, f1, p)];
const ONESHOTS = [
  ['mech_tick', (S) => S.tick()],
  ...[0, 1, 2].map((i) => [`mech_relay_${i}`, (S) => S.relay(i)]),
  ['mech_relay_pulse', (S, s) => [0, 1, 2].forEach((i) => s.setTimeout(() => S.relay(i), i * 500))],   // index.html ~8515
  ['mech_spark', (S) => S.spark(), { takes: 3 }],
  ...[0, 1, 2].map((i) => [`mech_answer_${i}`, (S) => S.answer(i)]),
  servo(0.12, 900, 1300, 0.02), servo(0.22, 300, 520, 0.035), servo(0.22, 320, 560, 0.035), servo(0.4, 400, 1600, 0.025),
  servo(0.24, 340, 620, 0.035), servo(2.0, 180, 420, 0.03), servo(0.12, 500, 900, 0.04), servo(0.2, 500, 900, 0.025),
  servo(0.15, 400, 700, 0.02), servo(0.35, 900, 1500, 0.02), servo(0.5, 260, 520, 0.03), servo(0.6, 300, 700, 0.025),
  servo(0.25, 500, 820, 0.02), servo(0.3, 300, 500, 0.02), servo(0.2, 400, 520, 0.02), servo(0.2, 120, 160, 0.012),
  servo(0.3, 300, 420, 0.02), servo(0.22, 700, 1250, 0.025),
  ['mech_click', (S) => S.click()],
  ['mech_grit', (S) => S.grit(), { takes: 2 }],
  ['d17_chirp', (S) => S.chirp()],
  ['d17_worried', (S) => S.worried()],
  ['d17_tap', (S) => S.tap()],
  ['mech_rattle_500', (S) => S.rattle(0.5)],
  ['mech_rattle_900', (S) => S.rattle(0.9)],
  ['d17_step', (S) => S.step(1), { takes: 4 }],
  ['d17_jump', (S) => S.jump()],
  ['d17_land', (S) => S.land(1)],
  ['mech_lamp_click', (S) => S.lampClick()],
  ['elec_buzz_short', (S) => S.buzzShort()],
  ['mech_ratchet', (S) => S.ratchet()],
  ['mech_door_rumble', (S) => S.doorRumble()],
  ['mech_door_open', (S) => S.doorOpen()],
  ['d17_strain', (S) => S.strain()],
  ['env_drip', (S) => S.drip(1), { takes: 3 }],
  ['elec_crackle', (S) => S.crackle(1), { takes: 3 }],
  ['env_groan', (S) => S.groan()],
  ['mech_scrape', (S) => S.scrape()],
  ['d17_bonk', (S) => S.bonk()],
  ...[0.3, 0.4, 0.5, 0.6, 0.7, 0.8].map((d) => [`mech_creak_${Math.round(d * 1000)}`, (S) => S.creak(d)]),
  ['mech_clank', (S) => S.clank()],
  ...[0.3, 0.5, 0.55, 0.6, 1.0, 1.2, 1.5, 2.0, 2.2, 2.5, 3.0].map((d) => [`mech_chain_${Math.round(d * 1000)}`, (S) => S.chain(d), { len: d + 4 }]),
  ['mech_thud', (S) => S.thud()],
  ['env_distant', (S) => S.distant()],
  ['mech_plate', (S) => S.plate()],
  ['mech_gate_tick', (S) => S.gateTick(), { takes: 3 }],
  ['mech_gate_slam', (S) => S.gateSlam(1)],
  ['d17_lift', (S) => S.lift()],
  ['d17_setdown_floor', (S) => S.setDown(false)],
  ['d17_setdown_deck', (S) => S.setDown(true)],
  ['mech_squeak', (S) => S.squeak(), { takes: 3 }],
  ...[0, 1, 2, 3, 4, 5].map((i) => [`mech_row_on_${i}`, (S) => S.rowOn(i)]),
  ['d17_knock', (S) => S.knock()],
  ['mech_scan_sweep', (S) => S.scanSweep()],
  ['mech_reject', (S) => S.reject()],
  ['mech_hatch_lift', (S) => S.hatchLift()],
  ['mech_bell', (S) => S.bell()],
  ['mech_klaxon', (S) => S.klaxon()],
  ['mech_belt_stop', (S) => S.beltStop()],
  ['mech_clunk', (S) => S.clunk()],
  ['mech_clack', (S) => S.clack(1)],
  ['mech_tumble', (S) => S.tumble(), { takes: 2 }],
  ['mech_pawl_click', (S) => S.pawlClick()],
  ['mech_pawl_clatter', (S) => S.pawlClatter(), { takes: 3 }],
  ['mech_lift_crash', (S) => S.liftCrash(1)],
  ['mech_lift_crash_v040', (S) => S.liftCrash(0.4)],
  ['mech_lurch', (S) => S.lurch()],
  ['mech_alarm_bell', (S) => S.alarmBell()],
  ['mech_crate_land', (S) => S.crateLand(1)],
  ['curio_found', (S) => S.found()],
  ...['scale', 'stamp', 'mug', 'mugDown', 'sit', 'wind', 'coin', 'switch', 'paper'].map((k) => [`curio_${k.replace(/[A-Z]/g, (c) => '_' + c.toLowerCase())}`, (S) => S.curio(k)]),
  ['curio_radio', (S) => S.radio(), { len: 12 }],
  ['env_splash', (S) => S.splash(1)],
  ['elec_zap', (S) => S.zap(1), { takes: 3 }],
  ...['crush', 'shock', 'grabbed', 'fall'].map((h) => [`death_${h}`, (S) => S.death(h), { takes: 2 }]),
];

// Continuous Sound layers: their graphs are fixed and only their level follows the game, so a loop at level 1 is the
// whole sound. [name, call, loop length (s), periodic?, sends to the depot reverb?]. The game's noise buffers loop
// every 2 s and every oscillator here fits whole cycles into 2 s, so those layers repeat exactly every 2 s.
const LOOPS = [
  ['loop_hum', (S) => S.hum(1), 2, true, false],
  ['loop_buzz', (S) => S.buzz(1), 2, true, false],
  ['loop_hiss', (S) => S.hiss(1), 2, true, false],
  ['loop_roll', (S) => S.roll(1), 2, true, false],
  ['loop_tubes', (S) => S.tubes(1), 2, true, false],
  ['loop_belt', (S) => S.belt(1), 2, true, false],
  ['loop_drum', (S) => S.drum(1), 2, true, false],
  ['loop_air', (S) => S.air(1), 100 / 9, false, true],        // its 0.09 Hz swell: one period, noise crossfaded
  ['loop_drag', (S) => S.drag(1), 2, true, true],
];

// Ambient emitters (Ambience, index.html ~1147-1211): continuous kinds as loops at level 1 and full reach, event kinds
// as one-shots (one blip each), the music box as one turn of its tune. [name, emitter, loop length, periodic?]
const AMB_LOOPS = [
  ['amb_buzz_loop', { kind: 'buzz' }, 7.7, true],             // 100 Hz saw, 0.13 Hz swell: 770 cycles, 1.001 swells
  ['amb_hum_loop', { kind: 'hum' }, 2, true],
  ['amb_lap_loop', { kind: 'lap' }, 200 / 31, false],         // two periods of its 0.31 Hz swell
  ['amb_wind_loop', { kind: 'wind' }, 20, false, 2],          // 0.07 and 0.05 Hz: exact only at 100 s, so 20 s with a 2 s crossfade
  ['amb_static_loop', { kind: 'static' }, 2, true],
  ['amb_machine_loop', { kind: 'machine' }, 10, true],        // 0.9 Hz swell: 9 periods in 10 s
];
const AMB_BLIPS = [['amb_drip', 'drip', 3], ['amb_tick', 'tick', 1], ['amb_fan', 'fan', 3]];

const TREATS = ['tannoy', 'dispatch', 'card', 'card_worn', 'child', 'elder', 'machine', 'radio'];

// ---------------------------------------------------------------------------------------------------------------
const want = process.argv.slice(2);
const pick = (name) => !want.length || want.some((w) => name.includes(w));
const manifest = [], wetSkipped = [];
let bytes = 0;

function save(name, chs, meta) {
  const mono = isMono(chs), out = mono ? [chs[0]] : chs;
  const r = writeWav(path.join(OUT, meta.dir || '', `${name}.wav`), out);
  const st = stats(out);
  bytes += r.bytes;
  manifest.push({ file: `${meta.dir ? meta.dir + '/' : ''}${name}.wav`, channels: out.length, seconds: +st.dur.toFixed(3), peakDb: +dbfs(st.peak).toFixed(1), rmsDb: +dbfs(st.rms).toFixed(1), bytes: r.bytes, clipped: r.clipped, ...meta.info });
  if (r.clipped) console.warn(`  ! ${name}: ${r.clipped} samples clipped`);
  console.log(`${name.padEnd(34)} ${out.length}ch ${st.dur.toFixed(3)}s peak ${dbfs(st.peak).toFixed(1)} dBFS`);
}

async function oneShot(name, call, opts = {}) {
  const takes = opts.takes || 1;
  for (let k = 0; k < takes; k++) {
    const id = takes > 1 ? `${name}_v${k + 1}` : name;
    let dryLen = 0;
    for (const wet of k === 0 && opts.wet !== false ? [false, true] : [false]) {
      const s = new Session(opts.len || 6, hash(id));
      const S = s.sound();
      if (!wet) S.send.disconnect();            // dry: the depot reverb's return is cut; wet: dry + return, as heard
      call(S, s);
      const chs = trim(await s.render());
      // A quiet sound's reverb return can sit wholly under the -60 dBFS trim: its wet file would be the dry one again.
      if (wet && chs[0].length / SR < dryLen + 0.05) { console.log(`${(id + '_wet').padEnd(34)} skipped: return under -60 dBFS`); wetSkipped.push(id); continue; }
      if (!wet) dryLen = chs[0].length / SR;
      save(wet ? `${id}_wet` : id, chs, { info: { kind: 'oneshot', source: 'Sound', wet } });
    }
  }
}

async function soundLoop(name, call, L, periodic, sends) {
  for (const wet of sends ? [false, true] : [false]) {
    const warm = 6, X = periodic ? 0.05 : 0.5;
    const s = new Session(warm + L + X + 0.1, hash(name));
    const S = s.sound();
    if (!wet) S.send.disconnect();
    call(S, s);
    const chs = loopify(await s.render(), warm, L, X, !periodic);
    save(wet ? `${name}_wet` : name, chs, { info: { kind: 'loop', source: 'Sound', wet, loopSeconds: +L.toFixed(4) } });
  }
}

function ambience(s) {
  const S = s.sound();
  const { src } = moduleSource('Ambience');
  const p = patch(src, [['bus.gain.value = 0.9;', 'bus.gain.value = 1;', 'the emitter bus 0.9 is left to the Unity mixer']]);
  return new Function('Sound', 'setTimeout', 'Math', `${p}\nreturn Ambience;`)(S, s.setTimeout, s.Math);
}
// Drive Ambience.update every frame (60 Hz) on the virtual clock, with him standing on the emitter (k = 1).
function driveAmbience(s, A, e, until) {
  for (let t = 0; t <= until; t += 1 / 60) s.at(t, () => A.update([e], e.x, e.region));
}

async function ambLoop(name, kind, L, periodic, X0) {
  const warm = 3, X = X0 || (periodic ? 0.05 : 0.5);
  const s = new Session(warm + L + X + 0.1, hash(name));
  const A = ambience(s), e = { region: 1, x: 0, reach: 1, level: 1, ...kind };
  driveAmbience(s, A, e, warm + L + X + 0.1);
  save(name, loopify(await s.render(), warm, L, X, !periodic), { info: { kind: 'loop', source: 'Ambience', loopSeconds: +L.toFixed(4) } });
}

async function ambBlip(name, kind, takes) {
  // Driven every frame like the game, standing on the emitter. Its gain glides up from 0 (tau 0.25 s) when it is first
  // heard, so the blips are taken from after 2 s, at full level: successive blips are the takes (each is randomized).
  const s = new Session(14, hash(name));
  const A = ambience(s), e = { region: 1, x: 0, reach: 1, level: 1, kind, period: 1.0 };
  driveAmbience(s, A, e, 13.5);
  const chs = await s.render();
  const on = onsets(chs[0], 0.002, 0.2).filter((t) => t > 2 && t < 13);
  for (let k = 0; k < takes; k++) {
    const id = takes > 1 ? `${name}_v${k + 1}` : name;
    const a = Math.round(on[k] * SR) - 48, b = Math.round(on[k + 1] * SR) - 48;
    save(id, trim(chs.map((c) => c.slice(a, b))), { info: { kind: 'oneshot', source: 'Ambience' } });
  }
}

// Onset times (s): 1 ms frames whose peak rises past `thr` from below 60 % of it, at least `gap` s apart.
function onsets(c, thr, gap) {
  const out = [], hop = 48;
  let prev = 0;
  for (let i = 0; i + hop < c.length; i += hop) {
    let m = 0; for (let j = i; j < i + hop; j++) m = Math.max(m, Math.abs(c[j]));
    if (m > thr && prev < m * 0.6 && (!out.length || i / SR - out[out.length - 1] > gap)) out.push(i / SR);
    prev = m;
  }
  return out;
}

async function musicBox() {
  // One turn of the tune: 11 notes ~0.42-0.48 s apart, then four 0.6 s rests (index.html ~1182-1191). Rendered for two
  // turns and more from a full-level emitter driven every frame; the caller cuts the second turn out as the loop.
  const s = new Session(18, hash('amb_musicbox'));
  const A = ambience(s), e = { region: 1, x: 0, reach: 1, level: 1, kind: 'musicbox' };
  driveAmbience(s, A, e, 17);
  return s.render();
}

async function voice() {
  const s = new Session(6, hash('voice_tannoy_chime'));
  const S = s.sound();
  const { src } = moduleSource('Voice');
  const p = patch(src, [['return {\n    play, stop, init,', 'return { __chain: chain, __TREAT: TREAT, __crackle: crackleBuffer, __impulse: impulse,\n    play, stop, init,', 'expose the chain to the renderer']]);
  const doc = { getElementById: () => ({ innerHTML: '', classList: { add() {}, remove() {} }, appendChild() {} }), createElement: () => ({}) };
  const V = new Function('Sound', 'Music', 'Telemetry', 'document', 'setTimeout', 'clearTimeout', 'Math', `${p}\nreturn Voice;`)(
    S, { duck() {} }, { event() {} }, doc, s.setTimeout, s.clearTimeout, s.Math);
  return { s, S, V, src };
}

async function tannoyChime() {
  // The chime the tannoy plays before its voice, through the tannoy's own chain (shaper, band-pass, room, echo).
  // The chime's loop is taken from index.html verbatim and run with the chain's head as its input.
  const { s, V, src } = await voice();
  V.init();
  const t = V.__TREAT.tannoy, ch = V.__chain(t);
  ch.out.gain.value = 1;                                   // the game sets this to the voice's level (0.85 first play)
  const body = blockSource(src, 'for (const [f0, dt0] of [[659.3, 0.05], [523.3, 0.6]])');
  new Function('ctx', 'ch', 'c', body)(s.proxy, ch, { nodes: [] });
  save('voice_tannoy_chime', trim(await s.render()), { info: { kind: 'oneshot', source: 'Voice' } });
}

async function crackleBeds() {
  // The crackle and hiss bed every voice plays under it, per treatment: the game's lines, verbatim, into c.out.
  const { src } = moduleSource('Voice');
  const a = src.indexOf('const cr = ctx.createBufferSource();'), b = src.indexOf('cr.start(); c.nodes.push(cr);') + 'cr.start(); c.nodes.push(cr);'.length;
  const body = src.slice(a, b);
  for (const name of TREATS) {
    const { s, V } = await voice();
    V.init();
    const t = V.__TREAT[name], out = s.ctx.createGain(); out.connect(s.S.output());
    new Function('ctx', 't', 'c', 'crackleBuffer', body)(s.proxy, t, { out, nodes: [] }, V.__crackle);
    const chs = await s.render();
    save(`voice_crackle_${name}`, chs.map((c) => c.slice(0, 3 * SR)), { info: { kind: 'loop', source: 'Voice', loopSeconds: 3 } });
  }
}

async function impulses() {
  // The reverb impulses, for a convolution reverb in Unity: the depot's (Sound.start) and each voice room (Voice).
  const s = new Session(1, 7);
  s.sound();
  const ir = s.S.send.buffer;
  save('ir_depot_2400ms', [ir.getChannelData(0), ir.getChannelData(1)], { dir: 'ir', info: { kind: 'ir', source: 'Sound' } });
  const { V } = await voice();
  V.init();
  for (const room of [...new Set(TREATS.map((n) => V.__TREAT[n].room))]) {
    const b = V.__impulse(room);
    save(`ir_voice_${Math.round(room * 1000)}ms`, [b.getChannelData(0), b.getChannelData(1)], { dir: 'ir', info: { kind: 'ir', source: 'Voice' } });
  }
}

// ---------------------------------------------------------------------------------------------------------------
mkdirSync(OUT, { recursive: true });
for (const [name, call, opts] of ONESHOTS) if (pick(name)) await oneShot(name, call, opts);
for (const [name, call, L, periodic, sends] of LOOPS) if (pick(name)) await soundLoop(name, call, L, periodic, sends);
for (const [name, kind, L, periodic, X] of AMB_LOOPS) if (pick(name)) await ambLoop(name, kind, L, periodic, X);
for (const [name, kind, takes] of AMB_BLIPS) if (pick(name)) await ambBlip(name, kind, takes);
if (pick('amb_musicbox')) {
  const chs = await musicBox();
  // A turn is 11 notes plus four rests; cut from the 12th onset (the second turn's first note) to the 23rd.
  const on = onsets(chs[0], 0.01, 0.3);
  const a = on[11], b = on[22];
  const seg = chs.map((c) => c.slice(Math.round(a * SR) - 48, Math.round(b * SR) - 48));
  save('amb_musicbox_loop', seg, { info: { kind: 'loop', source: 'Ambience', loopSeconds: +((b - a)).toFixed(4), onsets: on.slice(11, 22).map((t) => +(t - a).toFixed(3)) } });
}
if (pick('voice_tannoy')) await tannoyChime();
if (pick('voice_crackle')) await crackleBeds();
if (pick('ir_')) await impulses();

if (!want.length) {
  writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify({ rendered: new Date().toISOString().slice(0, 10), sampleRate: SR, wetSkipped, files: manifest }, null, 1));
  console.log(`\n${manifest.length} files, ${(bytes / 1e6).toFixed(2)} MB`);
}
