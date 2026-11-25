// Is there official material in the project's packages that names the events an HTML element has, so that a prefix (`on`) need not be
// data? Candidates: `typescript/lib/lib.dom.d.ts` (`interface GlobalEventHandlers`, the project's own TypeScript, if it has one) and the
// declarations `astro` ships for its JSX (`astro/astro-jsx.d.ts`, `astro/dist/...`). Measured: do they exist in the project's packages,
// and do they list the event attributes (`onclick`, `onend`) and not `one`.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(`${process.cwd()}/`);
const astroDir = path.dirname(require.resolve('astro/package.json'));
const exists = (p) => (fs.existsSync(p) ? `${fs.statSync(p).size} bytes` : 'absent');
console.log('astro', JSON.parse(fs.readFileSync(path.join(astroDir, 'package.json'), 'utf8')).version);
let dom = null;
try { dom = require.resolve('typescript/lib/lib.dom.d.ts'); } catch { /* not installed */ }
console.log('typescript/lib/lib.dom.d.ts from the project:', dom ?? 'not resolvable (the project has no typescript)');
const candidates = ['astro-jsx.d.ts', 'dist/types/public/elements.d.ts', 'dist/types/public/index.d.ts', 'dist/types/astro-jsx.d.ts', 'types.d.ts'];
for (const c of candidates) console.log(`astro/${c}:`, exists(path.join(astroDir, c)));
const found = [];
const visit = (d) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name === 'node_modules') continue; const f = path.join(d, e.name); if (e.isDirectory()) visit(f); else if (e.name.endsWith('.d.ts')) found.push(f); } };
visit(astroDir);
const words = ['onclick', 'onend', 'GlobalEventHandlers', 'on:click', 'onClick'];
const hits = {};
for (const f of found) {
  const text = fs.readFileSync(f, 'utf8');
  for (const w of words) if (text.includes(w)) (hits[w] ??= []).push(`${path.relative(astroDir, f)}(${text.split(w).length - 1})`);
}
console.log(`.d.ts files under astro: ${found.length}`);
for (const w of words) console.log(`  "${w}" in:`, (hits[w] ?? ['none']).slice(0, 8).join(', '));
if (dom) {
  const text = fs.readFileSync(dom, 'utf8');
  console.log(`lib.dom.d.ts: ${text.length} chars; declares GlobalEventHandlers ${text.includes('interface GlobalEventHandlers {')}; names onclick ${text.includes(' onclick:')}, onend ${text.includes(' onend:')}, one ${text.includes(' one:')}`);
}
