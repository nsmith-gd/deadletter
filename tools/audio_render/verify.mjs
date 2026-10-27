// Spot-checks five renders against what the synth code says they should be: duration, peak and RMS envelope.
//   node verify.mjs
// Each model below is read off the game's code (index.html, Sound): tone(freq, dur, type, peak) shapes its gain with
// env(): 0.0001 -> peak over 4 ms (exponential), then peak -> 0.0001 over `dur` (exponential). The expected RMS of a
// partial is its envelope times the waveform's RMS factor (sine 1/sqrt 2, square 1, sawtooth 1/sqrt 3); partials at
// different pitches add in power. The expected length is where the summed envelope falls below -60 dBFS (the trim).
import path from 'node:path';
import { readWav, OUT, dbfs } from './lib.mjs';

const RMS = { sine: Math.SQRT1_2, square: 1, sawtooth: 1 / Math.sqrt(3), triangle: 1 / Math.sqrt(3) };
// One tone(): start time t0, duration, waveform, peak (the code's own numbers).
const tone = (t0, dur, type, peak) => ({ t0, dur, type, peak });
function env(p, t) {
  const a = 0.004, lo = 0.0001;
  if (t < p.t0) return 0;
  const u = t - p.t0;
  if (u < a) return lo * Math.pow(p.peak / lo, u / a);
  if (u < a + p.dur) return p.peak * Math.pow(lo / p.peak, (u - a) / p.dur);
  return u < p.dur + 0.05 ? lo : 0;
}

const CHECKS = [
  // strain() { tone(780, 0.16, 'sine', 0.035, 0.3, 980); }
  { file: 'd17_strain', code: "tone(780, 0.16, 'sine', 0.035)", parts: [tone(0, 0.16, 'sine', 0.035)] },
  // tick() { tone(1900, 0.03, 'square', 0.03, 0.2); }
  { file: 'mech_tick', code: "tone(1900, 0.03, 'square', 0.03)", parts: [tone(0, 0.03, 'square', 0.03)] },
  // groan() { tone(48, 1.4, 'sawtooth', 0.02, 1.0, 41); }
  { file: 'env_groan', code: "tone(48, 1.4, 'sawtooth', 0.02)", frame: 0.0625, parts: [tone(0, 1.4, 'sawtooth', 0.02)] },   // 3 periods of 48 Hz a frame
  // bell() { tone(1568, 0.5, 'sine', 0.04, 0.8); setTimeout(() => tone(1175, 0.7, 'sine', 0.035, 0.8), 160); }
  { file: 'mech_bell', code: "tone(1568, 0.5, sine, 0.04) + 160 ms: tone(1175, 0.7, sine, 0.035)", parts: [tone(0, 0.5, 'sine', 0.04), tone(0.16, 0.7, 'sine', 0.035)] },
  // reject() { [0, 0.32].forEach((d) => setTimeout(() => { tone(196, 0.26, 'square', 0.05, 0.5); tone(207, 0.26, 'square', 0.04, 0.5); }, d * 1000)); }
  // 196 and 207 Hz beat at 11 Hz: a frame is one beat (1/11 s), over which the two add in power.
  { file: 'mech_reject', code: '2 x (tone(196, 0.26, square, 0.05) + tone(207, 0.26, square, 0.04)), 320 ms apart', frame: 1 / 11,
    parts: [0, 0.32].flatMap((d) => [tone(d, 0.26, 'square', 0.05), tone(d, 0.26, 'square', 0.04)]) },
];

let worst = 0;
for (const c of CHECKS) {
  const { sr, chs } = readWav(path.join(OUT, c.file + '.wav'));
  const x = chs[0], n = x.length;
  const peak = x.reduce((m, v) => Math.max(m, Math.abs(v)), 0);
  const ampAt = (t) => c.parts.reduce((s, p) => s + env(p, t), 0);
  // Two square partials 11 Hz apart beat: their envelopes add in amplitude at the crests, so the expected peak is the sum.
  const expPeak = Math.max(...Array.from({ length: 2000 }, (_, i) => ampAt(i / 1000)));
  let expEnd = 0; for (let t = 0; t < 3; t += 0.0005) if (ampAt(t) > 0.001) expEnd = t;
  const FRAME = c.frame || 0.01;
  const rows = [];
  let maxDev = 0;
  for (let f = 0; (f + 1) * FRAME * sr <= n; f++) {
    const a = Math.round(f * FRAME * sr), b = Math.round((f + 1) * FRAME * sr);
    let s = 0; for (let i = a; i < b; i++) s += x[i] * x[i];
    const got = Math.sqrt(s / (b - a));
    // Expected: mean power of each partial over the frame (sampled each 0.1 ms), summed.
    let e = 0; for (let k = 0; k < 100; k++) { const t = (f + k / 100) * FRAME; for (const p of c.parts) e += (env(p, t) * RMS[p.type]) ** 2; }
    const want = Math.sqrt(e / 100);
    if (dbfs(want) > -50) maxDev = Math.max(maxDev, Math.abs(dbfs(got) - dbfs(want)));
    rows.push([f * FRAME * 1000, dbfs(got), dbfs(want)]);
  }
  worst = Math.max(worst, maxDev);
  console.log(`\n${c.file}: ${c.code}`);
  console.log(`  length  ${(n / sr * 1000).toFixed(1)} ms (expected ${(expEnd * 1000 + 5).toFixed(1)} ms: -60 dBFS point + 5 ms fade)`);
  console.log(`  peak    ${dbfs(peak).toFixed(2)} dBFS (envelope peak ${dbfs(expPeak).toFixed(2)} dBFS; band-limited square/saw overshoot adds up to ~1 dB)`);
  console.log(`  RMS envelope, ${(FRAME * 1000).toFixed(1)} ms frames, measured / expected dBFS (frames above -50 dBFS expected: max deviation ${maxDev.toFixed(2)} dB):`);
  const step = Math.max(1, Math.ceil(rows.length / 12));
  console.log('   ' + rows.filter((_, i) => i % step === 0).map(([t, g, w]) => `${t.toFixed(0)}ms ${g.toFixed(1)}/${w.toFixed(1)}`).join('  '));
}
console.log(`\nworst envelope deviation: ${worst.toFixed(2)} dB`);

// Loop seams: the step from the last sample back to the first, against the loop's typical sample-to-sample step.
import { readFileSync } from 'node:fs';
const man = JSON.parse(readFileSync(path.join(OUT, 'manifest.json'), 'utf8'));
console.log('\nloop seams (seam step / RMS step; ~1 or below reads as continuous):');
for (const f of man.files.filter((q) => q.kind === 'loop')) {
  const { chs } = readWav(path.join(OUT, f.file));
  const ratios = chs.map((x) => {
    let s = 0; for (let i = 1; i < x.length; i++) s += (x[i] - x[i - 1]) ** 2;
    return Math.abs(x[0] - x[x.length - 1]) / Math.sqrt(s / (x.length - 1));
  });
  console.log(`  ${f.file.padEnd(32)} ${Math.max(...ratios).toFixed(2)}`);
}
