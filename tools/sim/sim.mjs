// Timed first playthroughs, DL-01 to DL-05, by the simulated player in ../sim/bot.js.
// node sim.mjs <firstSeed> <count> <out.jsonl> [mechanical]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const [seed0 = '1', count = '1', OUT = 'sim.jsonl', mode = ''] = process.argv.slice(2);
const BOT = fs.readFileSync(path.resolve('../sim/bot.js'), 'utf8');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server', '--autoplay-policy=no-user-gesture-required'] });
for (let n = 0; n < +count; n++) {
  const seed = +seed0 + n;
  const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', (r) => r.fulfill({ path: path.join(path.resolve('node_modules/three'), r.request().url().split('three@0.169.0/')[1]), contentType: 'text/javascript' }));
  await page.route('https://fonts.**', (r) => r.abort());
  await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html' + (process.env.QUERY || ''));
  await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
  await page.addScriptTag({ content: BOT });
  await page.evaluate(([s, m, s0, ch]) => window.__startBot(s, { mechanical: m === 'mechanical', steps: 10, trace: s0, chapter: ch }), [seed, mode, process.env.TRACE || '', process.env.CHAPTER || '']);
  // CHAPTER=att plays Chapter 1 Attendance from its first checkpoint instead of the prologue.
  // CHAPTER=att2 starts at DL-15 (the sick bay balcony, out of the duct).
  // Or a later chapter 1 checkpoint by name: dorm, corridor, sickbay, crossing, kitchen, workshop.
  const CP = { att: 'school', att2: 'sickbay', dorm: 'dorm', corridor: 'corridor', sickbay: 'sickbay', crossing: 'crossing', kitchen: 'kitchen', workshop: 'workshop' }[process.env.CHAPTER];
  if (CP) { await page.selectOption('#scene-select', CP); await page.click('#scene-go'); } else await page.click('#begin');
  const t0 = Date.now();
  let out;
  while (Date.now() - t0 < 40 * 60000) {
    await new Promise((r) => setTimeout(r, 2000));
    out = await page.evaluate(() => ({ ...window.__sim.out, x: window.__dl01.game.x, clock: window.__dl01.game.clock, mode: window.__dl01.game.mode, act: window.__dl01.game.act && window.__dl01.game.act.kind, hold: window.__dl01.game.hold }));
    if (out.done) break;
    if (errs.length) { out.error = 'page error: ' + errs[0]; break; }
    if (process.env.PROGRESS && (Date.now() - t0) % 30000 < 2100) console.log('  ..', Math.round(out.clock), 'x=' + out.x.toFixed(2), Object.keys(out.marks).pop(), out.events.slice(-1)[0] || '', out.mode, out.act, out.hold, errs.slice(-2).join(' | '));
  }
  if (!out.done) out.error = 'wall timeout at x=' + out.x;
  if (out.error) await page.screenshot({ path: `simfail_${seed}.png` });
  out.wall = Math.round((Date.now() - t0) / 1000); out.pageErrors = errs.slice(0, 5);
  if (out.trace) fs.writeFileSync(OUT + ".trace", out.trace.join("\n")); delete out.trace; fs.appendFileSync(OUT, JSON.stringify(out) + '\n');
  console.log(seed, out.error || 'ok', JSON.stringify(out.marks), out.wall + 's wall');
  await page.close();
}
await browser.close();
