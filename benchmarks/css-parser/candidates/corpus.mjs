// CSSTree over the real stylesheets of the npm packages installed at image build (data only: nothing is executed).
// usage: node corpus.mjs   (env CSSTREE = module to test, TAG = output suffix, CORPUS, OUT)
const csstree = await import(process.env.CSSTREE || 'css-tree');
import fs from 'node:fs';
import path from 'node:path';

const HERE = import.meta.dirname;
const ROOT = process.env.CORPUS || path.join(HERE, 'corpus/node_modules');
const OUT = process.env.OUT || path.join(HERE, 'out');
fs.mkdirSync(OUT, { recursive: true });

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

const pkgOf = (p) => {
  const rel = path.relative(ROOT, p).split(path.sep);
  return rel[0].startsWith('@') ? `${rel[0]}/${rel[1]}` : rel[0];
};
const kidsOf = (n) => (n && n.children ? n.children.toArray() : []);

const perPackage = {};
const byKind = {}; // what the Raw nodes are: key -> {count, packages:Set, sample}
const samples = {}; // `${pkg}|${message}` -> up to 2 samples
const worst = [];
const T0 = () => ({ files: 0, bytes: 0, rules: 0, decls: 0, atrules: 0, rawStatements: 0, rawPreludes: 0, rawValues: 0, errors: 0, threw: 0, filesWithErrors: 0, ms: 0 });
const total = T0();
const note = (key, pkg, sample) => {
  const k = (byKind[key] ||= { count: 0, packages: new Set(), sample });
  k.count++; k.packages.add(pkg);
};
for (const file of files) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch { continue; }
  if (text.length > 8_000_000) continue;
  const pkg = pkgOf(file);
  const P = (perPackage[pkg] ||= T0());
  const errors = [];
  const t0 = process.hrtime.bigint();
  let ast;
  try {
    ast = csstree.parse(text, { positions: true, onParseError: (e) => errors.push(e) });
  } catch (e) {
    P.threw++; total.threw++; P.files++; total.files++;
    note(`THREW ${e.constructor.name}`, pkg, file);
    continue;
  }
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  P.ms += ms; total.ms += ms;
  let rules = 0, decls = 0, atrules = 0, rawStmt = 0, rawPrelude = 0, rawValue = 0;
  const snip = (n) => JSON.stringify(text.slice(n.loc.start.offset, Math.min(n.loc.end.offset, n.loc.start.offset + 70)));
  const visit = (node, inRule, parentAt) => {
    for (const ch of kidsOf(node)) {
      if (ch.type === 'Rule') {
        rules++;
        if (ch.prelude.type === 'Raw') { rawPrelude++; note('Raw prelude of a rule', pkg, `${path.basename(file)} ${snip(ch)}`); }
        visit(ch.block, true, parentAt);
      } else if (ch.type === 'Atrule') {
        atrules++;
        if (ch.prelude && ch.prelude.type === 'Raw') { rawPrelude++; note(`Raw prelude of @${ch.name}`, pkg, `${path.basename(file)} ${snip(ch)}`); }
        if (ch.block) visit(ch.block, inRule, ch.name);
      } else if (ch.type === 'Declaration') {
        decls++;
        if (ch.value.type === 'Raw' && !ch.property.startsWith('--')) { rawValue++; note(`Raw value of ${ch.property}`, pkg, `${path.basename(file)} ${snip(ch)}`); }
      } else if (ch.type === 'Raw') {
        rawStmt++;
        const t = text.slice(ch.loc.start.offset, ch.loc.end.offset).trimStart();
        const where = parentAt ? `inside @${parentAt}` : inRule ? 'inside a rule' : 'at top level';
        const head = t.startsWith('@') ? `starts with @${t.slice(1).match(/^[\w-]*/)[0]}` : '.#:[&>'.includes(t[0] || ' ') ? 'starts with a selector' : /^[A-Za-z*]/.test(t) ? 'starts with an identifier' : `starts with ${JSON.stringify(t[0] || '')}`;
        note(`Raw statement ${where}, ${head}`, pkg, `${path.basename(file)} ${snip(ch)}`);
      }
    }
  };
  try { visit(ast, false, null); } catch (e) { note(`VISIT THREW ${e.constructor.name}`, pkg, file); }
  for (const e of errors) {
    const key = `${pkg}|${e.message}`;
    (samples[key] ||= { count: 0, items: [] }).count++;
    if (samples[key].items.length < 2) samples[key].items.push(`${path.relative(path.join(ROOT, pkg), file)}:${e.line}:${e.column}  ${JSON.stringify(text.slice(Math.max(0, e.offset - 40), e.offset + 60))}`);
  }
  for (const X of [P, total]) {
    X.files++; X.bytes += text.length; X.rules += rules; X.decls += decls; X.atrules += atrules; X.rawStatements += rawStmt; X.rawPreludes += rawPrelude;
    X.rawValues += rawValue; X.errors += errors.length; if (errors.length) X.filesWithErrors++;
  }
  if (errors.length) worst.push([errors.length, `${pkg}/${path.relative(path.join(ROOT, pkg), file)}`, text.length]);
}
worst.sort((a, b) => b[0] - a[0]);
const out = [];
const w = (s) => out.push(s);
w(`module: ${process.env.CSSTREE || 'css-tree'}`);
w(`corpus: ${total.files} .css files, ${(total.bytes / 1e6).toFixed(1)} MB, parse time ${total.ms.toFixed(0)} ms (positions on)`);
w(`rules ${total.rules}, declarations ${total.decls}, at-rules ${total.atrules}`);
w(`files with at least one parse error: ${total.filesWithErrors}; parse errors in all: ${total.errors}; parse threw: ${total.threw}`);
w(`Raw nodes: ${total.rawStatements} at statement level, ${total.rawPreludes} Raw preludes (rule or at-rule), ${total.rawValues} Raw values of non-custom properties`);
w('\n## per package: files, KB, rules, decls, atrules, files-with-errors, errors, rawStatements, rawPreludes, rawValues');
for (const [name, P] of Object.entries(perPackage).sort((a, b) => b[1].errors - a[1].errors)) {
  w(`${name.padEnd(36)} ${String(P.files).padStart(4)} ${String((P.bytes / 1024) | 0).padStart(7)} ${String(P.rules).padStart(7)} ${String(P.decls).padStart(7)} ${String(P.atrules).padStart(5)} err-files ${String(P.filesWithErrors).padStart(3)} errors ${String(P.errors).padStart(5)} rawStmt ${String(P.rawStatements).padStart(4)} rawPrelude ${String(P.rawPreludes).padStart(4)} rawValue ${String(P.rawValues).padStart(4)}`);
}
w('\n## what the Raw nodes are (count, packages, one sample)');
for (const [k, v] of Object.entries(byKind).sort((a, b) => b[1].count - a[1].count)) {
  w(`${String(v.count).padStart(6)}  ${k}   [${[...v.packages].slice(0, 6).join(', ')}${v.packages.size > 6 ? ', …' : ''}]`);
  w(`          e.g. ${v.sample}`);
}
w('\n## parse errors per package and message (count, up to 2 samples)');
for (const [key, v] of Object.entries(samples).sort((a, b) => b[1].count - a[1].count)) {
  w(`${String(v.count).padStart(6)}  ${key}`);
  for (const s of v.items) w(`          ${s}`);
}
w('\n## files with most errors');
for (const [n, f, size] of worst.slice(0, 12)) w(`${String(n).padStart(5)}  ${f}  (${size} bytes)`);
fs.writeFileSync(`${OUT}/corpus${process.env.TAG || ''}.txt`, out.join('\n') + '\n');
console.log(out.slice(0, 6).join('\n'));
