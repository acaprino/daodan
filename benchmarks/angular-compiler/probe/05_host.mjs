// Host metadata: what Angular's own helpers give for host: {...} (strings only? spans?), typings of the inputs of createHostElement.
import { C, fs, q, p } from './_lib.mjs';
const nm = '/fixture/node_modules';
const c = fs.readFileSync(`${nm}/@angular/compiler/types/_index-chunk.d.ts`, 'utf8') + fs.readFileSync(`${nm}/@angular/compiler/types/compiler.d.ts`, 'utf8');
for (const needle of ['interface HostObjectLiteralBinding', 'interface HostBindingDecorator', 'interface HostListenerDecorator']) {
  const i = c.indexOf(needle);
  console.log(`--- ${needle}: ${i < 0 ? 'NOT FOUND' : '\n' + c.slice(i, i + 700)}`);
}
// Attempt: build the three HostObjectLiteralBinding by hand with spans computed from the .ts text.
const file = '/fixture/src/app/inline.component.ts';
const text = fs.readFileSync(file, 'utf8');
const pf = new C.ParseSourceFile(text, file);
const loc = (off) => {
  let line = 0, col = 0;
  for (let i = 0; i < off; i++) { if (text[i] === '\n') { line++; col = 0; } else col++; }
  return new C.ParseLocation(pf, off, line, col);
};
const span = (a, b) => new C.ParseSourceSpan(loc(a), loc(b));
const entries = [["'(click)'", "'onHost()'"], ["'(window:keydown.escape)'", "'onEsc()'"], ["'[class.active]'", "'active'"]];
const lits = entries.map(([k, v]) => {
  const ks = text.indexOf(k), vs = text.indexOf(v, ks);
  return { key: { text: k.slice(1, -1), span: span(ks + 1, ks + k.length - 1) }, value: { text: v.slice(1, -1), span: span(vs + 1, vs + v.length - 1) }, sourceSpan: span(ks, vs + v.length) };
});
console.log('hand-built literal bindings (shape is a guess from the typings printed above):', lits.length);
try {
  const he = C.createHostElement('component', 'app-inline', span(text.indexOf('InlineComponent'), text.indexOf('InlineComponent') + 15), lits, [], []);
  console.log('createHostElement ->', he ? he.constructor.name : he);
  if (he) for (const ev of he.listeners) console.log(`  listener name=${q(ev.name)} target=${q(ev.target)} type=${ev.type} handler.source=${q(ev.handler.source)} sourceSpan ${p(ev.sourceSpan.start)}..${p(ev.sourceSpan.end)} covers ${q(text.slice(ev.sourceSpan.start.offset, ev.sourceSpan.end.offset))} handlerSpan covers ${q(text.slice(ev.handlerSpan.start.offset, ev.handlerSpan.end.offset))}`);
} catch (e) { console.log('createHostElement threw:', e.stack.split('\n').slice(0, 4).join(' | ')); }
console.log('\n--- createHostElement source (fesm):');
console.log(C.createHostElement.toString().slice(0, 2500));
const i2 = c.indexOf('interface SourceNode');
console.log('--- SourceNode typings:', i2 < 0 ? 'NOT FOUND' : c.slice(i2 - 200, i2 + 900));
