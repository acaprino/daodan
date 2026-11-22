// What the parser keeps as Raw on the corpus (statements, rule preludes) read again whole as the contents of a block by the
// same parser, with the positions of the source: how many read cleanly, how many are still Raw, in which packages.
// usage: modal_css_parser.py::probe_run --script benchmarks/css-parser/probes/reread_raw.mjs (README.md, "Choices")
// Raw statements and Raw rule preludes of the corpus, read again whole as the contents of a block by the fork itself.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const cs = createRequire('/engines/package.json')('@eslint/css-tree');
const ROOT = '/corpus/node_modules';
const files = [];
const walk = (d, depth = 0) => { let es; try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; } for (const e of es) { const p = path.join(d, e.name); if (e.isDirectory()) { if (depth < 12) walk(p, depth + 1); } else if (e.isFile() && e.name.toLowerCase().endsWith('.css')) files.push(p); } };
walk(ROOT);
const kids = (n) => (n && n.children ? n.children.toArray() : []);
const stats = { raw_statement: 0, raw_rule: 0, ok: 0, still_raw: 0, empty: 0, threw: 0 };
const bad = [];
const byPkg = {};
for (const file of files) {
  let text; try { text = fs.readFileSync(file, 'utf8'); } catch { continue; }
  if (text.length > 8_000_000) continue;
  const rel = path.relative(ROOT, file);
  const ast = cs.parse(text, { positions: true, parseCustomProperty: true });
  const found = [];
  const visit = (list) => { for (const ch of kids(list)) {
    if (ch.type === 'Rule') { if (ch.prelude.type === 'Raw') found.push(['raw_rule', ch.loc, ch.prelude.value]); visit(ch.block); }
    else if (ch.type === 'Atrule') { if (ch.block) visit(ch.block); }
    else if (ch.type === 'Raw') { if (ch.value.split(';').some((x) => x.trim())) found.push(['raw_statement', ch.loc, ch.value]); }
  } };
  visit(ast);
  for (const [kind, loc, val] of found) {
    stats[kind]++;
    const raw = text.slice(loc.start.offset, loc.end.offset);
    let reparsed;
    try {
      reparsed = cs.parse('x{' + raw + '}', { positions: true, parseCustomProperty: true, offset: loc.start.offset - 2, line: loc.start.line, column: loc.start.column - 2 });
    } catch (e) { stats.threw++; continue; }
    const inner = kids(kids(reparsed)[0] && kids(reparsed)[0].block);
    let still = 0;
    const walk2 = (l) => { for (const ch of kids(l)) { if (ch.type === 'Raw' && ch.value.split(';').some((x) => x.trim())) still++; if (ch.type === 'Rule') { if (ch.prelude.type === 'Raw') still++; walk2(ch.block); } if (ch.type === 'Atrule' && ch.block) walk2(ch.block); } };
    walk2(kids(reparsed)[0].block);
    if (still === 0) { stats.ok++; byPkg[rel.split('/')[0]] = (byPkg[rel.split('/')[0]] || 0) + 1; } else { stats.still_raw++; if (bad.length < 8) bad.push(`${rel}:${loc.start.line} ${kind} ${JSON.stringify(raw.slice(0, 160))} -> still ${still}`); }
    // positions: the first inner node's line equals the raw's line
  }
}
console.log(JSON.stringify(stats), JSON.stringify(byPkg));
console.log(bad.join('\n'));
// a position check on a small case
const t = 'a{}\n\n.k { @container (min-width: 1px) {\n  & .b { c: d }\n  & .e { f: g } } }';
const ast = cs.parse(t, { positions: true });
const raw = [];
const v = (l) => { for (const ch of kids(l)) { if (ch.type === 'Raw') raw.push(ch); if (ch.block) v(ch.block); } };
v(ast);
for (const r of raw) {
  const rr = t.slice(r.loc.start.offset, r.loc.end.offset);
  const re = cs.parse('x{' + rr + '}', { positions: true, offset: r.loc.start.offset - 2, line: r.loc.start.line, column: r.loc.start.column - 2 });
  console.log(JSON.stringify(rr), JSON.stringify(cs.toPlainObject(cs.clone(re)), (k, val) => (k === 'loc' ? undefined : val)).slice(0, 600));
  const rule = kids(kids(re)[0].block);
  console.log(rule.map((x) => x.type + '@' + x.loc.start.line + ':' + x.loc.start.offset + ' ' + JSON.stringify(t.slice(x.loc.start.offset, x.loc.end.offset))).join(' | '));
}
