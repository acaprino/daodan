// node corpus_tools.mjs TOOL : the corpus files (data only) through one adapter; counts, errors, throws, time.
import fs from 'node:fs';
import path from 'node:path';
import { adapters } from './adapters.mjs';

const HERE = import.meta.dirname;
const OUT = process.env.OUT || path.join(HERE, 'out');

const tool = process.argv[2];
const ROOT = process.env.CORPUS || path.join(HERE, 'corpus/node_modules');
const files = [];
const walk = (dir, depth = 0) => {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (depth < 12) walk(p, depth + 1); }
    else if (e.isFile() && e.name.toLowerCase().endsWith('.css')) files.push(p);
  }
};
walk(ROOT);
const pkgOf = (p) => { const r = path.relative(ROOT, p).split(path.sep); return r[0].startsWith('@') ? `${r[0]}/${r[1]}` : r[0]; };
const T0 = () => ({ files: 0, bytes: 0, rules: 0, decls: 0, atrules: 0, comments: 0, filesWithError: 0, errors: 0, threw: 0, ms: 0 });
const total = T0();
const per = {};
const messages = {};
const note = (msg, file, n = 1) => { const m = (messages[msg] ||= { count: 0, sample: file }); m.count += n; };
for (const file of files) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch { continue; }
  if (text.length > 8_000_000) continue;
  const pkg = pkgOf(file);
  const P = (per[pkg] ||= T0());
  const t0 = process.hrtime.bigint();
  const r = adapters[tool](text);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  for (const X of [P, total]) {
    X.files++; X.bytes += text.length; X.ms += ms;
    if (r.threw) { X.threw++; X.filesWithError++; X.errors++; }
    else {
      X.rules += r.rules.length; X.decls += r.decls.length; X.atrules += r.atrules.length; X.comments += r.comments.length;
      X.errors += r.errors; if (r.errors) X.filesWithError++;
    }
  }
  const rel = `${pkg}/${path.relative(path.join(ROOT, pkg), file)}`;
  if (r.threw) note(r.threw.replace(/\d+/g, 'N').slice(0, 90), rel);
  else if (r.errorMessages) for (const m of r.errorMessages) note(m.replace(/\d+/g, 'N').slice(0, 90), rel);
}
const out = [];
const w = (s) => out.push(s);
w(`tool: ${tool}`);
w(`corpus: ${total.files} files, ${(total.bytes / 1e6).toFixed(1)} MB, time ${total.ms.toFixed(0)} ms (adapter included)`);
w(`rules ${total.rules}, declarations ${total.decls}, at-rules ${total.atrules}, comments ${total.comments}   (files that threw are counted in none of these)`);
w(`files with an error: ${total.filesWithError}; errors: ${total.errors}; files that threw: ${total.threw}`);
w('\n## per package: files, errors, threw, rules, decls, atrules');
for (const [n, X] of Object.entries(per).sort((a, b) => b[1].errors - a[1].errors).slice(0, 14)) w(`${n.padEnd(34)} ${String(X.files).padStart(4)} err ${String(X.errors).padStart(6)} threw ${String(X.threw).padStart(4)} rules ${String(X.rules).padStart(7)} decls ${String(X.decls).padStart(8)} at ${String(X.atrules).padStart(5)}`);
w('\n## messages (count, first file)');
for (const [m, v] of Object.entries(messages).sort((a, b) => b[1].count - a[1].count).slice(0, 14)) w(`${String(v.count).padStart(6)}  ${m}   [${v.sample}]`);
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, `corpus_${tool}.txt`), out.join('\n') + '\n');
console.log(out.slice(0, 4).join('\n'));
