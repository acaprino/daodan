// Depth limits of CSSTree's parser, walker and generator, each stage alone. usage: node depth.mjs   (env CSSTREE = module to test, TAG = output suffix, OUT)
const csstree = await import(process.env.CSSTREE || 'css-tree');
import fs from 'node:fs';
import path from 'node:path';

const OUT = process.env.OUT || path.join(import.meta.dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const lines = [];
const w = (s) => lines.push(s);

const forms = {
  'rules nested with &': (n) => 'a{' + '&{'.repeat(n) + 'b:c' + '}'.repeat(n + 1),
  'at-rules nested (@media)': (n) => '@media print{'.repeat(n) + 'a{b:c}' + '}'.repeat(n),
  'parentheses in a value': (n) => 'a{b:' + '('.repeat(n) + '1' + ')'.repeat(n) + '}',
  'calc( in a value': (n) => 'a{b:' + 'calc('.repeat(n) + '1' + ')'.repeat(n) + '}',
  ':is( in a selector': (n) => ':is('.repeat(n) + 'a' + ')'.repeat(n) + '{b:c}',
  ':not( in a selector': (n) => ':not('.repeat(n) + 'a' + ')'.repeat(n) + '{b:c}',
  'blocks {} in a custom property': (n) => 'a{--b:' + '{'.repeat(n) + '}'.repeat(n) + '}',
};
const stage = (fn) => {
  const t0 = process.hrtime.bigint();
  try {
    const r = fn();
    return { ok: true, r, ms: Number(process.hrtime.bigint() - t0) / 1e6 };
  } catch (e) {
    return { ok: false, err: `${e && e.constructor && e.constructor.name}: ${String(e && e.message).slice(0, 60)}`, ms: Number(process.hrtime.bigint() - t0) / 1e6 };
  }
};
for (const [name, make] of Object.entries(forms)) {
  w(`\n## ${name}`);
  for (const n of [100, 300, 1000, 3000, 10000, 50000]) {
    const src = make(n);
    let errors = 0;
    let ast;
    const p = stage(() => { ast = csstree.parse(src, { positions: true, onParseError: () => { errors++; } }); return 'parsed'; });
    let nodes = 0;
    const walked = p.ok ? stage(() => { csstree.walk(ast, () => { nodes++; }); return nodes; }) : null;
    const gen = p.ok ? stage(() => csstree.generate(ast).length) : null;
    const plain = p.ok ? stage(() => JSON.stringify(csstree.toPlainObject(ast)).length) : null;
    const f = (x) => (x ? (x.ok ? `ok(${typeof x.r === 'number' ? x.r : ''})` : `THREW ${x.err}`) : '-');
    w(`n=${String(n).padStart(5)}: parse ${p.ok ? 'ok' : 'THREW ' + p.err} (errors ${errors}, ${p.ms.toFixed(1)} ms) | walk ${f(walked)} | generate ${f(gen)} | toPlainObject ${f(plain)}`);
  }
}
fs.writeFileSync(`${OUT}/depth${process.env.TAG || ''}.txt`, lines.join('\n') + '\n');
console.log(lines.join('\n'));
