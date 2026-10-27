// Shared plumbing for the offline renders: pull the game's own synth modules out of index.html, run them in an
// OfflineAudioContext (node-web-audio-api) on a virtual clock, and write 48 kHz 16-bit WAVs.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { OfflineAudioContext } from 'node-web-audio-api';

const here = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(here, '../..');
export const SRC = path.join(ROOT, 'game/undelivered/index.html');
export const OUT = path.join(ROOT, 'art/sfx/out');
export const SR = 48000;

const html = readFileSync(SRC, 'utf8');
const lineOf = (i) => html.slice(0, i).split('\n').length;

// The source of one `const Name = (() => { ... })();` module, verbatim, and its line range in index.html.
export function moduleSource(name) {
  const head = `const ${name} = (() => {`;
  const a = html.indexOf(head);
  if (a < 0) throw new Error(`module ${name} not found in index.html`);
  const b = html.indexOf('\n})();', a);
  return { src: html.slice(a, b + 6), from: lineOf(a), to: lineOf(b + 1) };
}

// A block of source starting at `start` up to its balanced closing brace (for the tannoy chime's loop).
export function blockSource(within, start) {
  const a = within.indexOf(start);
  if (a < 0) throw new Error(`block not found: ${start}`);
  let i = within.indexOf('{', a), depth = 0;
  for (; i < within.length; i++) { if (within[i] === '{') depth++; else if (within[i] === '}' && --depth === 0) break; }
  return within.slice(a, i + 1);
}

// Small, documented edits to the extracted source (each must match exactly once). Nothing else is changed.
export function patch(src, edits) {
  for (const [from, to, why] of edits) {
    const n = src.split(from).length - 1;
    if (n !== 1) throw new Error(`patch (${why}) matched ${n} times`);
    src = src.replace(from, to);
  }
  return src;
}

// Deterministic Math.random, so every render is repeatable (the game's own noise is Math.random too).
export function seededMath(seed) {
  let s = seed >>> 0;
  const m = Object.create(Math);
  m.random = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  return m;
}
export const hash = (str) => { let h = 2166136261; for (const c of str) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };

// An offline context with a virtual clock. The game schedules with ctx.currentTime and setTimeout; here currentTime
// reads the virtual `now`, and setTimeout callbacks are run in time order with `now` set to when they were due, so
// every node is scheduled at exactly the time the game would schedule it, before rendering starts.
export class Session {
  constructor(seconds, seed = 1) {
    this.ctx = new OfflineAudioContext({ numberOfChannels: 2, length: Math.ceil(SR * seconds), sampleRate: SR });
    this.now = 0; this.timers = []; this.seq = 0; this.Math = seededMath(seed);
    const ctx = this.ctx, self = this;
    this.proxy = new Proxy(ctx, {
      get(t, p) { if (p === 'currentTime') return self.now; const v = t[p]; return typeof v === 'function' ? v.bind(t) : v; },
      set(t, p, v) { t[p] = v; return true; },
    });
    this.setTimeout = (fn, ms = 0) => { const id = ++this.seq; this.timers.push({ at: this.now + Math.max(0, Number(ms) || 0) / 1000, fn, id }); return id; };
    this.clearTimeout = (id) => { this.timers = this.timers.filter((t) => t.id !== id); };
  }
  // Run every pending timer due before `until` (seconds), in order.
  run(until = Infinity) {
    for (;;) {
      this.timers.sort((a, b) => a.at - b.at || a.id - b.id);
      const t = this.timers[0];
      if (!t || t.at > until) break;
      this.timers.shift(); this.now = t.at; t.fn();
    }
  }
  at(sec, fn) { this.setTimeout(fn, sec * 1000); }
  async render() { this.run(); const buf = await this.ctx.startRendering(); return [buf.getChannelData(0).slice(), buf.getChannelData(1).slice()]; }

  // The game's Sound module, extracted verbatim, living in this context. window.AudioContext hands back the proxy.
  sound() {
    const { src } = moduleSource('Sound');
    const proxy = this.proxy;
    const window = { AudioContext: function AudioContext() { return proxy; } };
    const S = new Function('window', 'setTimeout', 'Math', `${src}\nreturn Sound;`)(window, this.setTimeout, this.Math);
    S.start();
    S.output().gain.value = 1;          // the master's 0.8 is left to the Unity mixer (see README)
    this.S = S;
    return S;
  }
}

export const dbfs = (x) => (x > 0 ? 20 * Math.log10(x) : -Infinity);

// Cut trailing samples below -60 dBFS (all channels), with a 5 ms fade on what is left, so nothing clicks.
export function trim(chs, floorDb = -60) {
  const thr = Math.pow(10, floorDb / 20);
  let last = 0;
  for (const c of chs) for (let i = c.length - 1; i > last; i--) if (Math.abs(c[i]) > thr) { last = i; break; }
  const n = Math.min(chs[0].length, last + 1 + Math.round(0.005 * SR));
  const fade = Math.round(0.005 * SR);
  return chs.map((c) => { const o = c.slice(0, n); for (let i = 0; i < fade && i < n; i++) o[n - 1 - i] *= i / fade; return o; });
}

// Seamless loop of length L from a rendered segment of length L + X: the head is crossfaded with what followed the
// end, so the end runs straight on into the start. `power` for uncorrelated (noise) content, linear for periodic.
export function loopify(chs, start, L, X, power) {
  const s = Math.round(start * SR), n = Math.round(L * SR), x = Math.round(X * SR);
  return chs.map((c) => {
    const o = c.slice(s, s + n);
    for (let i = 0; i < x; i++) {
      const k = i / x, a = power ? Math.sin(k * Math.PI / 2) : k, b = power ? Math.cos(k * Math.PI / 2) : 1 - k;
      o[i] = c[s + i] * a + c[s + n + i] * b;
    }
    return o;
  });
}

export function isMono(chs) { if (chs.length < 2) return true; const [a, b] = chs; for (let i = 0; i < a.length; i++) if (Math.abs(a[i] - b[i]) > 1e-6) return false; return true; }

export function writeWav(file, chs) {
  const n = chs[0].length, nc = chs.length, data = Buffer.alloc(n * nc * 2);
  let clipped = 0;
  for (let i = 0; i < n; i++) for (let c = 0; c < nc; c++) {
    let v = chs[c][i]; if (v > 1 || v < -1) { clipped++; v = Math.max(-1, Math.min(1, v)); }
    data.writeInt16LE(Math.round(v < 0 ? v * 32768 : v * 32767), (i * nc + c) * 2);
  }
  const h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + data.length, 4); h.write('WAVE', 8); h.write('fmt ', 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(nc, 22); h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * nc * 2, 28); h.writeUInt16LE(nc * 2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(data.length, 40);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, Buffer.concat([h, data]));
  return { clipped, bytes: 44 + data.length };
}

export function readWav(file) {
  const b = readFileSync(file), nc = b.readUInt16LE(22), sr = b.readUInt32LE(24);
  let p = 12; while (b.toString('ascii', p, p + 4) !== 'data') p += 8 + b.readUInt32LE(p + 4);
  const len = b.readUInt32LE(p + 4) / (2 * nc), chs = Array.from({ length: nc }, () => new Float32Array(len));
  for (let i = 0; i < len; i++) for (let c = 0; c < nc; c++) chs[c][i] = b.readInt16LE(p + 8 + (i * nc + c) * 2) / 32768;
  return { sr, chs };
}

export function stats(chs) {
  let peak = 0, sum = 0;
  for (const c of chs) for (const v of c) { const a = Math.abs(v); if (a > peak) peak = a; sum += v * v; }
  return { dur: chs[0].length / SR, peak, rms: Math.sqrt(sum / (chs.length * chs[0].length)) };
}
