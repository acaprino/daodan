import * as C from '@angular/compiler';
import fs from 'node:fs';
export { C, fs };

// Independent ground truth: line/col (0-based, '\n' breaks lines) of an offset in a text.
export function lc(text, off) {
  let line = 0, col = 0;
  for (let i = 0; i < off; i++) { if (text[i] === '\n') { line++; col = 0; } else col++; }
  return { line, col };
}
export const p = (l) => `${l.line}:${l.col}@${l.offset}`;
export const q = (s) => JSON.stringify(s);

// R3 template nodes (have sourceSpan, no `span`; expression ASTs have `span`).
const SKIP = new Set(['sourceSpan', 'startSourceSpan', 'endSourceSpan', 'handlerSpan', 'keySpan', 'valueSpan', 'nameSpan', 'i18n', 'handler', 'value']);
const label = (n) => n.constructor.name + (n.name ? `<${n.name}>` : n.tagName ? `<${n.tagName}>` : '');
export function* walk(node, path = [], seen = new Set()) {
  if (Array.isArray(node)) { for (const n of node) yield* walk(n, path, seen); return; }
  if (!node || typeof node !== 'object' || seen.has(node)) return;
  if ('span' in node || !('sourceSpan' in node)) return;
  seen.add(node);
  yield { node, kind: node.constructor.name, path };
  const p2 = [...path, label(node)];
  for (const [k, v] of Object.entries(node)) { if (!SKIP.has(k)) yield* walk(v, p2, seen); }
}

export function* events(nodes) {
  for (const w of walk(nodes)) {
    if (Array.isArray(w.node.outputs)) for (const ev of w.node.outputs) yield { ev, owner: w.node, path: [...w.path, label(w.node)].join(' > ') };
  }
}

// Render an expression AST compactly (no spans).
const ASTSKIP = new Set(['span', 'sourceSpan', 'nameSpan', 'keySpan', 'argumentSpan', 'location', 'source', 'errors', 'absoluteOffset']);
export function render(a) {
  if (Array.isArray(a)) return '[' + a.map(render).join(', ') + ']';
  if (a === null || typeof a !== 'object') return JSON.stringify(a);
  const k = a.constructor.name;
  if (k === 'ASTWithSource') return render(a.ast);
  const parts = Object.entries(a).filter(([key]) => !ASTSKIP.has(key)).map(([key, v]) => `${key}=${render(v)}`);
  return `${k}(${parts.join(', ')})`;
}

// Name of the callee as source-like text, plus receiver and method name.
export function chain(a) {
  const k = a.constructor.name;
  if (k === 'ImplicitReceiver') return '';
  if (k === 'ThisReceiver') return 'this';
  if (k === 'PropertyRead' || k === 'SafePropertyRead') { const r = chain(a.receiver); return (r ? r + (k === 'SafePropertyRead' ? '?.' : '.') : '') + a.name; }
  if (k === 'KeyedRead') return `${chain(a.receiver)}[${render(a.key)}]`;
  if (k === 'Call' || k === 'SafeCall') return `${chain(a.receiver)}(...)`;
  return `<${k}>`;
}
export function describeCall(a) {
  const callee = a.receiver;
  const ck = callee.constructor.name;
  let receiver = null, method = null;
  if (ck === 'PropertyRead' || ck === 'SafePropertyRead') {
    method = callee.name;
    const rk = callee.receiver.constructor.name;
    receiver = rk === 'ImplicitReceiver' ? '<implicit component member>' : rk === 'ThisReceiver' ? '<this>' : chain(callee.receiver);
  } else { method = `<callee ${ck}>`; receiver = null; }
  return { kind: a.constructor.name, callee: chain(callee), receiver, method, nameSpan: callee.nameSpan, callSpan: a.sourceSpan };
}
export class CallCollector extends C.RecursiveAstVisitor {
  calls = [];
  visitCall(ast, ctx) { this.calls.push(describeCall(ast)); return super.visitCall(ast, ctx); }
  visitSafeCall(ast, ctx) { this.calls.push(describeCall(ast)); return super.visitSafeCall(ast, ctx); }
}
export function collectCalls(handler) { const c = new CallCollector(); c.visit(handler.ast ?? handler); return c.calls; }

// Compare a ParseSourceSpan with an expected [startOffset, endOffset) in `text`.
export function cmpSpan(text, span, exp, shift = 0) {
  const sOff = span.start.offset + shift, eOff = span.end.offset + shift;
  const covered = text.slice(sOff, eOff);
  const expStart = lc(text, exp[0]), expEnd = lc(text, exp[1]);
  const startOK = sOff === exp[0] && span.start.line === expStart.line && span.start.col === expStart.col;
  const endOK = eOff === exp[1] && span.end.line === expEnd.line && span.end.col === expEnd.col;
  return {
    exact: startOK && endOK,
    offsetsOK: sOff === exp[0] && eOff === exp[1],
    text: `${p(span.start)} .. ${p(span.end)} covers ${q(covered)}`,
    delta: startOK && endOK ? '' : ` expected ${expStart.line}:${expStart.col}@${exp[0]} .. ${expEnd.line}:${expEnd.col}@${exp[1]} (${q(text.slice(exp[0], exp[1]))}); delta start offset ${sOff - exp[0]}, end offset ${eOff - exp[1]}`,
  };
}

// expected spans for an event attribute written `attr` found once in `text` (value = text inside quotes)
export function expectedFor(text, attr, handler, nameInside) {
  const i = text.indexOf(attr);
  if (i < 0) return null;
  if (text.indexOf(attr, i + 1) >= 0) throw new Error('attr not unique: ' + attr);
  const eq = attr.indexOf('="');
  const vStart = i + eq + 2;
  const nameStart = i + (attr.startsWith('[(') ? 2 : 1);
  return { source: [i, i + attr.length], key: [nameStart, nameStart + nameInside.length], handler: [vStart, vStart + handler.length] };
}

// [attribute text as written, name as written inside the delimiters, handler text]
export const HTML_EVENTS = [
  ['(click)="save()"', 'click', 'save()'],
  ['(click)="this.save()"', 'click', 'this.save()'],
  ['(click)="svc.cancel()"', 'click', 'svc.cancel()'],
  ['(click)="!busy && save()"', 'click', '!busy && save()'],
  ['(click)="busy ? close() : reopen()"', 'click', 'busy ? close() : reopen()'],
  ['(click)="save(); close()"', 'click', 'save(); close()'],
  ['(click)="open = !open"', 'click', 'open = !open'],
  ["(click)=\"router.navigate(['/orders'])\"", 'click', "router.navigate(['/orders'])"],
  ['(click)="pay()"', 'click', 'pay()'],
  ['(click)="withIcon()"', 'click', 'withIcon()'],
  ['(ngSubmit)="submit()"', 'ngSubmit', 'submit()'],
  ['[(ngModel)]="q"', 'ngModel', 'q'],
  ['(keyup.enter)="search()"', 'keyup.enter', 'search()'],
  ['(click)="inIf()"', 'click', 'inIf()'],
  ['(click)="liClick(o)"', 'click', 'liClick(o)'],
  ['(click)="remove(o)"', 'click', 'remove(o)'],
  ['(click)="removeFor(o)"', 'click', 'removeFor(o)'],
  ['(click)="inTpl()"', 'click', 'inTpl()'],
  ['(window:resize)="onResize()"', 'window:resize', 'onResize()'],
  ['(saved)="onSaved($event)"', 'saved', 'onSaved($event)'],
];

// Print every bound event of `nodes`, compared with ground truth in `text` (spans shifted by `shift`).
export function reportEvents(nodes, text, expectedList, shift = 0, out = console.log) {
  const found = [...events(nodes)];
  out(`bound events found by walking the nodes: ${found.length}`);
  const rows = [];
  const matched = new Set();
  found.forEach(({ ev, path }, n) => {
    const handlerSrc = ev.handler.source ?? '(no source)';
    const exp = expectedList.find(([, , h], idx) => h === handlerSrc && !matched.has(idx));
    const idx = exp ? expectedList.indexOf(exp) : -1;
    if (idx >= 0) matched.add(idx);
    out(`\n[#${n}] path: ${path}`);
    out(`   name=${q(ev.name)} type=${ev.type} target=${q(ev.target)} phase=${q(ev.phase)}  handler.source=${q(handlerSrc)}  handler AST kind=${ev.handler.ast?.constructor.name}`);
    out(`   handler AST: ${render(ev.handler)}`);
    const row = { attr: exp ? exp[0] : `?${handlerSrc}`, found: 'yes' };
    if (exp) {
      const e = expectedFor(text, exp[0], exp[2], exp[1]);
      for (const [lbl, span, ex] of [['sourceSpan', ev.sourceSpan, e.source], ['keySpan', ev.keySpan, e.key], ['handlerSpan', ev.handlerSpan, e.handler]]) {
        const c = cmpSpan(text, span, ex, shift);
        out(`   ${lbl.padEnd(11)} ${c.exact ? 'EXACT  ' : 'DIFFERS'} ${c.text}${c.delta}`);
        row[lbl] = c.exact ? 'yes' : `no: ${c.delta.trim() || c.text}`;
      }
    } else out('   (no expectation matched this event)');
    const calls = collectCalls(ev.handler);
    out(`   calls: ${calls.length ? '' : '(none)'}`);
    for (const c of calls) {
      out(`     ${c.kind}: callee=${q(c.callee)} receiver=${q(c.receiver)} method=${q(c.method)}  nameSpan ${c.nameSpan ? `${c.nameSpan.start}..${c.nameSpan.end} covers ${q(text.slice(c.nameSpan.start + shift, c.nameSpan.end + shift))}` : '(none)'}  callSpan ${c.callSpan ? `${c.callSpan.start}..${c.callSpan.end} covers ${q(text.slice(c.callSpan.start + shift, c.callSpan.end + shift))}` : '(none)'}`);
    }
    row.calls = calls.map((c) => `${c.receiver ?? '?'}.${c.method}`).join(' ; ') || `(none; AST ${ev.handler.ast?.constructor.name})`;
    rows.push(row);
  });
  expectedList.forEach(([attr], i) => { if (!matched.has(i)) { out(`\nMISSING: ${attr}`); rows.push({ attr, found: 'NO' }); } });
  return rows;
}
