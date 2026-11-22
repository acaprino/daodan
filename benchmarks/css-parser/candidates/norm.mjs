// node norm.mjs TOOL  -> $OUT/norm_TOOL.json : every input of inputs.json through one adapter, plus the position checks.
import fs from 'node:fs';
import path from 'node:path';
import { adapters, caps } from './adapters.mjs';

const HERE = import.meta.dirname;
const OUT = process.env.OUT || path.join(HERE, 'out');

const tool = process.argv[2];
const inputs = JSON.parse(fs.readFileSync(path.join(HERE, 'inputs.json'), 'utf8'));
fs.mkdirSync(OUT, { recursive: true });

function lineStarts(src, conv) {
  const starts = [0];
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if (c === '\r') { if (src[i + 1] === '\n') i++; starts.push(i + 1); }
    else if (c === '\n' || (conv === 'spec' && c === '\f')) starts.push(i + 1);
  }
  return starts;
}
const lcOf = (starts, off) => {
  let lo = 0, hi = starts.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (starts[m] <= off) lo = m; else hi = m - 1; }
  return { line: lo + 1, column: off - starts[lo] + 1 };
};
const offsetOf = (starts, line, col) => (line >= 1 && line <= starts.length ? starts[line - 1] + col - 1 : -1);

const items = [];
const P = { nodes: 0, startSpec: 0, startEditor: 0, startNoText: 0, lcOffset: 0, lcOffsetOk: 0, blockEnds: 0, endExcl: 0, endIncl: 0, endGiven: 0, endNone: 0, refMembership: 0, refMembershipOk: 0, startMismatch: [] };
const ref = adapters['css-tree'];
for (const inp of inputs) {
  const r = adapters[tool](inp.src);
  const spec = lineStarts(inp.src, 'spec'), editor = lineStarts(inp.src, 'editor');
  let refStarts = null;
  for (const p of r.pos) {
    if (p.line == null) continue;
    P.nodes++;
    if (p.text !== undefined) {
      const text = p.text;
      const okSpec = text !== '' && inp.src.startsWith(text, offsetOf(spec, p.line, p.col));
      const okEd = text !== '' && inp.src.startsWith(text, offsetOf(editor, p.line, p.col));
      P.startSpec += okSpec; P.startEditor += okEd;
      if (!okSpec && P.startMismatch.length < 8) P.startMismatch.push(`${inp.id} ${p.kind} ${p.line}:${p.col} text ${JSON.stringify(text)}`);
    } else {
      P.startNoText++;
      refStarts ||= new Set(ref(inp.src).pos.map((q) => `${q.line}:${q.col}`));
      P.refMembership++; P.refMembershipOk += refStarts.has(`${p.line}:${p.col}`);
    }
    if (p.offset !== undefined && p.offset !== null) {
      P.lcOffset++;
      const w = lcOf(spec, p.offset);
      P.lcOffsetOk += w.line === p.line && w.column === p.col;
    }
    if (p.endOffset !== undefined) {
      if (p.endOffset === null) P.endNone++;
      else {
        P.endGiven++;
        if (p.kind === 'rule' || (p.kind === 'atrule' && inp.src[p.endOffset - 1] === '}') || (p.kind === 'atrule' && inp.src[p.endOffset] === '}')) {
          P.blockEnds++;
          P.endExcl += inp.src[p.endOffset - 1] === '}';
          P.endIncl += inp.src[p.endOffset] === '}';
        }
      }
    }
  }
  const { pos, ...rest } = r;
  items.push({ id: inp.id, ...rest });
}
fs.writeFileSync(path.join(OUT, `norm_${tool}.json`), JSON.stringify({ tool, caps: caps[tool], position: P, items }));
const threw = items.filter((i) => i.threw).length;
console.log(`${tool}: ${items.length} inputs, threw ${threw}, positions ${JSON.stringify({ ...P, startMismatch: P.startMismatch.length })}`);
