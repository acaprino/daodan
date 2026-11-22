// How many Raw nodes of the corpus hold only `;` (the engine does not make a hole of them) and how many other Raw statements.
// usage: modal_css_parser.py::probe_run --script benchmarks/css-parser/probes/semicolon_raw.mjs (README.md, "Choices")
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const cs = createRequire('/engines/package.json')('@eslint/css-tree');
const ROOT = '/corpus/node_modules';
const files = [];
const walk = (d, depth = 0) => { let es; try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; } for (const e of es) { const p = path.join(d, e.name); if (e.isDirectory()) { if (depth < 12) walk(p, depth + 1); } else if (e.isFile() && e.name.toLowerCase().endsWith('.css')) files.push(p); } };
walk(ROOT);
const kids = (n) => (n && n.children ? n.children.toArray() : []);
let semi = 0, other = 0, filesWith = new Set();
for (const f of files) {
  const t = fs.readFileSync(f, 'utf8'); if (t.length > 8_000_000) continue;
  const ast = cs.parse(t, { positions: true, parseCustomProperty: true });
  const v = (l) => { for (const ch of kids(l)) { if (ch.type === 'Raw') { if (ch.value.split(';').every((x) => x.trim() === '')) { semi++; filesWith.add(f); } else other++; } if (ch.block) v(ch.block); } };
  v(ast);
}
console.log(JSON.stringify({ semicolon_only_raw: semi, files_with: filesWith.size, other_raw_statements: other }));
