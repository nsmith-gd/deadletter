// Lists every call into the synth modules (Sound.*, Voice.play, Music.*) in the web build, with the line, the full
// argument text (balanced parentheses) and the enclosing top-level function. Used to build the variant list in
// render.mjs and the trigger column of docs/unity/audio_inventory.md.
//   node callsites.mjs [--json] [--module Sound]
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
export const SRC = path.resolve(here, '../../game/undelivered/index.html');

export function callSites(module = 'Sound') {
  const lines = readFileSync(SRC, 'utf8').split('\n');
  const out = [];
  let fn = '(top level)';
  const re = new RegExp(`\\b${module}\\.([A-Za-z]+)\\??\\.?\\(`, 'g');
  lines.forEach((line, i) => {
    const m0 = line.match(/^(?:async )?function ([A-Za-z0-9_]+)|^const ([A-Za-z0-9_]+) = /);
    if (m0) fn = m0[1] || m0[2];
    let m;
    re.lastIndex = 0;
    while ((m = re.exec(line))) {
      let depth = 1, j = m.index + m[0].length;
      while (j < line.length && depth) { if (line[j] === '(') depth++; else if (line[j] === ')') depth--; j++; }
      out.push({ line: i + 1, fn, name: m[1], args: line.slice(m.index + m[0].length, j - 1).trim() });
    }
  });
  return out;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const mod = process.argv.includes('--module') ? process.argv[process.argv.indexOf('--module') + 1] : 'Sound';
  const sites = callSites(mod);
  if (process.argv.includes('--json')) console.log(JSON.stringify(sites, null, 1));
  else for (const s of sites) console.log(`${s.name}\t${s.line}\t${s.fn}\t${s.args}`);
}
