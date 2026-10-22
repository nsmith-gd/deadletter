// Interaction-overlap audit: from every checkpoint, sweep D-17 along the stretch of game up to the next checkpoint and
// list each spot where two interactions answer Use at once (game: auditNear). The list must be empty.
// node audit_near.mjs   (from a folder with playwright-core and three in node_modules, the game served on :8765)
import { chromium } from 'playwright-core';
import path from 'node:path';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server'] });
const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
await page.route('https://cdn.jsdelivr.net/npm/three@0.169.0/**', (r) => r.fulfill({ path: path.join(path.resolve('node_modules/three'), r.request().url().split('three@0.169.0/')[1]), contentType: 'text/javascript' }));
await page.route('https://fonts.**', (r) => r.abort());
await page.goto((process.env.GAME || 'http://127.0.0.1:8765') + '/index.html');
await page.waitForFunction(() => !document.getElementById('begin').disabled, null, { timeout: 300000 });
const order = await page.evaluate(() => window.__dl01.cpOrder);
let total = 0;
for (let i = Math.max(0, order.indexOf(process.env.FROM || order[0])); i < order.length; i++) {
  const cp = order[i];
  await page.evaluate((c) => window.__dl01.startAt(c), cp);
  await page.waitForFunction(() => window.__dl01.game.mode === 'play', null, { timeout: 120000 });
  await new Promise((r) => setTimeout(r, 600));
  const hits = await page.evaluate(([c, n]) => {
    const D = window.__dl01, cps = D.cps, x0 = cps[c].x, next = n && cps[n] && cps[n].region === cps[c].region ? cps[n].x : x0 + 12;
    return D.auditNear(Math.max(x0 - 3, 0), Math.max(next, x0) + 3);
  }, [cp, order[i + 1]]);
  // Report runs of the same clash once, with the x range it covers.
  const runs = [];
  for (const h of hits) {
    const key = h.all.join(' + '), last = runs[runs.length - 1];
    if (last && last.key === key && h.x - last.x1 < 0.05) last.x1 = h.x; else runs.push({ key, x0: h.x, x1: h.x, y: h.y });
  }
  total += runs.length;
  console.log(cp.padEnd(10), runs.length ? '' : 'clear', runs.map((r) => `\n   ${r.key}  at x ${r.x0}–${r.x1} (y ${r.y})`).join(''));
}
if (errs.length) console.log('page errors:', errs.slice(0, 3));
console.log(total ? `${total} overlaps` : 'no overlaps');
await browser.close();
process.exit(total ? 1 : 0);
