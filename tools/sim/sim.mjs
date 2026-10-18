// Timed first playthroughs, DL-01 to DL-05, by the simulated player in bot.js.
// node sim.mjs <firstSeed> <count> <out.jsonl> [mechanical]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const [seed0 = '1', count = '1', OUT = 'sim.jsonl', mode = ''] = process.argv.slice(2);
const BOT = fs.readFileSync(path.resolve(path.dirname(new URL(import.meta.url).pathname), 'bot.js'), 'utf8');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server', '--autoplay-policy=no-user-gesture-required'] });
for (let n = 0; n < +count; n++) {
  const seed = +seed0 + n;
  const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', (r) => r.fulfill({ path: path.join(path.resolve('node_modules/three'), r.request().url().split('three@0.169.0/')[1]), contentType: 'text/javascript' }));
  await page.route('https://fonts.**', (r) => r.abort());
  await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html');
  await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
  await page.addScriptTag({ content: BOT });
  await page.evaluate(([s, m]) => window.__startBot(s, { mechanical: m === 'mechanical', steps: 10 }), [seed, mode]);
  await page.click('#begin');
  const t0 = Date.now();
  let out;
  while (Date.now() - t0 < 40 * 60000) {
    await new Promise((r) => setTimeout(r, 2000));
    out = await page.evaluate(() => ({ ...window.__sim.out, x: window.__dl01.game.x, clock: window.__dl01.game.clock }));
    if (out.done) break;
  }
  if (!out.done) out.error = 'wall timeout at x=' + out.x;
  if (out.error) await page.screenshot({ path: `simfail_${seed}.png` });
  out.wall = Math.round((Date.now() - t0) / 1000); out.pageErrors = errs.slice(0, 5);
  fs.appendFileSync(OUT, JSON.stringify(out) + '\n');
  console.log(seed, out.error || 'ok', JSON.stringify(out.marks), out.wall + 's wall');
  await page.close();
}
await browser.close();
