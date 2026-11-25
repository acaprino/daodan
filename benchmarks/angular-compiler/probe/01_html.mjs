// Points 1, 3 and 4 for the external template (templateUrl).
import { C, fs, HTML_EVENTS, reportEvents, events, walk, q, p, render } from './_lib.mjs';

const file = '/fixture/src/app/app.component.html';
const text = fs.readFileSync(file, 'utf8');
console.log(`file ${file}: ${text.length} chars, CR count ${[...text].filter((c) => c === '\r').length}`);

const parsed = C.parseTemplate(text, file, {});
console.log('parsed keys:', Object.keys(parsed).join(', '));
console.log('errors:', parsed.errors === null ? 'null' : JSON.stringify(parsed.errors.map((e) => ({ msg: e.msg, level: e.level, span: e.span?.toString?.() })), null, 1));
console.log('top-level node kinds:', parsed.nodes.map((n) => n.constructor.name + (n.name ? `<${n.name}>` : '')).join(', '));

console.log('\n=== POINT 1 + 3: every bound event, spans vs ground truth, handler AST ===');
const rows = reportEvents(parsed.nodes, text, HTML_EVENTS);

console.log('\n=== SUMMARY TABLE (html) ===');
for (const r of rows) console.log(`${r.attr}\n    found=${r.found} sourceSpan=${r.sourceSpan} keySpan=${r.keySpan} handlerSpan=${r.handlerSpan}\n    calls: ${r.calls}`);

console.log('\n=== cross-check with the official visitor (tmplAstVisitAll + TmplAstRecursiveVisitor) ===');
class V extends C.TmplAstRecursiveVisitor { n = []; visitBoundEvent(e) { this.n.push(e.handler.source); } }
const v = new V();
C.tmplAstVisitAll(v, parsed.nodes);
console.log(`visitor saw ${v.n.length} bound events: ${v.n.map(q).join(' ')}`);
const mine = [...events(parsed.nodes)].map((e) => e.ev.handler.source);
console.log(`own walk saw ${mine.length}; same set: ${JSON.stringify([...v.n].sort()) === JSON.stringify([...mine].sort())}`);

console.log('\n=== POINT 4: label (text children) of every element/template that owns an event ===');
function flat(n) {
  const k = n.constructor.name;
  if (k === 'Text') return n.value;
  if (k === 'BoundText') return `{{${n.value.source}}}`;
  if (n.children) return n.children.map(flat).join('');
  return '';
}
for (const w of walk(parsed.nodes)) {
  const n = w.node;
  if (!Array.isArray(n.outputs) || n.outputs.length === 0) continue;
  const label = (n.children ?? []).map(flat).join('').trim();
  console.log(`\n<${n.name ?? n.tagName}> (${n.constructor.name}) outputs=[${n.outputs.map((o) => o.name + (o.target ? '@' + o.target : '')).join(',')}]`);
  console.log(`   children: ${(n.children ?? []).map((c) => `${c.constructor.name}(${c.constructor.name === 'Text' ? q(c.value) : c.constructor.name === 'BoundText' ? q(c.value.source) : c.name ?? ''}) ${p(c.sourceSpan.start)}..${p(c.sourceSpan.end)}`).join(' | ') || '(none)'}`);
  console.log(`   flattened label by walking Text/BoundText children: ${q(label)}`);
  console.log(`   attributes: ${(n.attributes ?? []).map((a) => `${a.name}=${q(a.value)}`).join(' ') || '(none)'}   inputs: ${(n.inputs ?? []).map((a) => `${a.name}[type ${a.type}]=${q(a.value.source ?? '')}`).join(' ') || '(none)'}   templateAttrs: ${(n.templateAttrs ?? []).map((a) => a.name).join(',') || '(none)'}`);
}

console.log('\n=== block nodes present (is @if/@for parsed as a block node?) ===');
for (const w of walk(parsed.nodes)) if (/Block|Template$/.test(w.kind)) console.log(`${w.kind}  path=${w.path.join(' > ') || '(top)'}  ${w.node.tagName ? 'tagName=' + w.node.tagName : ''} ${w.node.templateAttrs?.length ? 'templateAttrs=' + w.node.templateAttrs.map((a) => a.name).join(',') : ''} ${w.node.attributes?.length && w.kind === 'Template' ? 'attributes=' + w.node.attributes.map((a) => a.name).join(',') : ''}`);

console.log('\n=== twoWay / [(ngModel)] raw ===');
for (const w of walk(parsed.nodes)) {
  if (w.node.inputs?.some((i) => i.name === 'ngModel')) {
    const i = w.node.inputs.find((x) => x.name === 'ngModel');
    console.log(`input ngModel type=${i.type} value=${render(i.value)} ; outputs=${w.node.outputs.map((o) => `${o.name}(type ${o.type}) handler=${render(o.handler)} source=${q(o.handler.source)}`).join('; ')}`);
  }
}
